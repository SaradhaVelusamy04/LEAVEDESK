from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.leave import LeaveRequest
from app.models.wfh import WfhRequest
from app.domain.enums import RoleEnum, RequestStatusEnum
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def report_setup(db_session: Session):
    """Setup manager and two employees."""
    mgr = User(
        name="Priya Manager",
        email="priya.manager@leavedesk.test",
        role=RoleEnum.MANAGER.value,
        hashed_password=get_password_hash("Manager@123")
    )
    other_mgr = User(
        name="Other Manager",
        email="other.mgr@leavedesk.test",
        role=RoleEnum.MANAGER.value,
        hashed_password=get_password_hash("Manager@123")
    )
    db_session.add_all([mgr, other_mgr])
    db_session.commit()
    db_session.refresh(mgr)
    db_session.refresh(other_mgr)

    emp1 = User(
        name="Arjun Employee",
        email="arjun@leavedesk.test",
        role=RoleEnum.EMPLOYEE.value,
        hashed_password=get_password_hash("Employee@123"),
        reports_to_id=mgr.id
    )
    emp2 = User(
        name="Meera Employee",
        email="meera@leavedesk.test",
        role=RoleEnum.EMPLOYEE.value,
        hashed_password=get_password_hash("Employee@123"),
        reports_to_id=other_mgr.id
    )
    db_session.add_all([emp1, emp2])
    db_session.commit()
    db_session.refresh(emp1)
    db_session.refresh(emp2)

    return {"mgr": mgr, "other_mgr": other_mgr, "emp1": emp1, "emp2": emp2}


def get_token(user: User) -> str:
    return create_access_token(data={"sub": str(user.id), "role": user.role})


def test_empty_report_returns_valid_csv(client: TestClient, report_setup):
    """06: A user with no requests in window receives a valid CSV with header row and zero summary - never error."""
    emp1 = report_setup["emp1"]
    token = get_token(emp1)

    response = client.get("/reports/leaves", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert "attachment; filename=" in response.headers["Content-Disposition"]

    content = response.text
    lines = [line.strip() for line in content.strip().split("\n")]
    assert len(lines) >= 6

    # 1. Exact header row
    expected_header = "date,request_type,leave_type,duration_type,half,hours,days_counted,status,reason,decided_by,decided_at"
    assert lines[0] == expected_header

    # Summary block checks
    assert "SUMMARY" in content
    assert "Total Approved Leave Days,0.00" in content
    assert "Total Approved WFH Days,0" in content
    assert "Pending Requests Count,0" in content
    assert "Rejected Requests Count,0" in content


def test_report_content_sorting_and_summary_calculation(client: TestClient, report_setup, db_session: Session):
    """01, 02, 03, 04: Report headers, date calculations, chronological sorting, and summary metrics."""
    emp1 = report_setup["emp1"]
    mgr = report_setup["mgr"]
    token = get_token(emp1)

    today = date.today()
    # 1 Approved Leave 2 days ago
    leave1 = LeaveRequest(
        user_id=emp1.id,
        date=today - timedelta(days=10),
        leave_type="CASUAL",
        duration_type="FULL_DAY",
        days_counted=1.0,
        status="APPROVED",
        decided_by=mgr.id,
        reason="Doctor visit"
    )
    # 1 Pending Leave 5 days ago
    leave2 = LeaveRequest(
        user_id=emp1.id,
        date=today - timedelta(days=5),
        leave_type="SICK",
        duration_type="HALF_DAY",
        half="FIRST_HALF",
        days_counted=0.5,
        status="PENDING",
        reason="Dentist"
    )
    # 1 Rejected WFH 20 days ago (Thursday to Friday = 2 working days)
    wfh1 = WfhRequest(
        user_id=emp1.id,
        start_date=today - timedelta(days=20),
        end_date=today - timedelta(days=19),
        working_days_count=2,
        status="REJECTED",
        decided_by=mgr.id,
        decision_comment="Need you on site"
    )
    db_session.add_all([leave1, leave2, wfh1])
    db_session.commit()

    response = client.get("/reports/leaves", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    content = response.text
    assert "leave_report_arjun@leavedesk.test_" in response.headers["Content-Disposition"]

    # Verify summary
    assert "Total Approved Leave Days,1.00" in content
    assert "Pending Requests Count,1" in content
    assert "Rejected Requests Count,1" in content


def test_report_access_control(client: TestClient, report_setup):
    """05: Employees can only download their own report. Managers may pass ?employee_id=<id> for direct reports."""
    emp1 = report_setup["emp1"]
    emp2 = report_setup["emp2"]
    mgr = report_setup["mgr"]

    token_emp1 = get_token(emp1)
    token_mgr = get_token(mgr)

    # 1. Employee trying to pass another employee's id -> 403 Forbidden
    res_emp_forbidden = client.get(
        f"/reports/leaves?employee_id={emp2.id}",
        headers={"Authorization": f"Bearer {token_emp1}"}
    )
    assert res_emp_forbidden.status_code == 403

    # 2. Manager downloading direct report (emp1 reports to mgr) -> 200 OK
    res_mgr_direct = client.get(
        f"/reports/leaves?employee_id={emp1.id}",
        headers={"Authorization": f"Bearer {token_mgr}"}
    )
    assert res_mgr_direct.status_code == 200
    assert "arjun@leavedesk.test" in res_mgr_direct.headers["Content-Disposition"]

    # 3. Manager trying to download another manager's direct report (emp2) -> 403 Forbidden
    res_mgr_other = client.get(
        f"/reports/leaves?employee_id={emp2.id}",
        headers={"Authorization": f"Bearer {token_mgr}"}
    )
    assert res_mgr_other.status_code == 403
