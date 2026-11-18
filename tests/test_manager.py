from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.leave import LeaveRequest
from app.models.wfh import WfhRequest
from app.domain.enums import RoleEnum, RequestStatusEnum
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def manager_setup(db_session: Session):
    """Setup 2 managers and employees in separate teams."""
    mgr1 = User(
        name="Priya Manager",
        email="priya.manager@leavedesk.test",
        role=RoleEnum.MANAGER.value,
        hashed_password=get_password_hash("Manager@123")
    )
    mgr2 = User(
        name="Rohan Manager",
        email="rohan.manager@leavedesk.test",
        role=RoleEnum.MANAGER.value,
        hashed_password=get_password_hash("Manager@123")
    )
    db_session.add_all([mgr1, mgr2])
    db_session.commit()
    db_session.refresh(mgr1)
    db_session.refresh(mgr2)

    emp1 = User(
        name="Arjun Employee",
        email="arjun@leavedesk.test",
        role=RoleEnum.EMPLOYEE.value,
        hashed_password=get_password_hash("Employee@123"),
        reports_to_id=mgr1.id
    )
    emp2 = User(
        name="Meera Employee",
        email="meera@leavedesk.test",
        role=RoleEnum.EMPLOYEE.value,
        hashed_password=get_password_hash("Employee@123"),
        reports_to_id=mgr2.id  # Reports to Rohan!
    )
    db_session.add_all([emp1, emp2])
    db_session.commit()
    db_session.refresh(emp1)
    db_session.refresh(emp2)

    return {"mgr1": mgr1, "mgr2": mgr2, "emp1": emp1, "emp2": emp2}


def get_token(user: User) -> str:
    return create_access_token(data={"sub": str(user.id), "role": user.role})


def test_manager_queue_direct_reports_only(client: TestClient, manager_setup):
    """01: GET /manager/requests returns direct reports requests only, defaults to status=PENDING."""
    mgr1 = manager_setup["mgr1"]
    emp1 = manager_setup["emp1"]
    emp2 = manager_setup["emp2"]

    token_mgr1 = get_token(mgr1)
    token_emp1 = get_token(emp1)
    token_emp2 = get_token(emp2)

    target_date = (date.today() + timedelta(days=10)).isoformat()

    # Emp1 (reports to Priya/mgr1) creates leave
    client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token_emp1}"},
        json={"date": target_date, "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )

    # Emp2 (reports to Rohan/mgr2) creates leave
    client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token_emp2}"},
        json={"date": target_date, "leave_type": "SICK", "duration_type": "FULL_DAY"}
    )

    # Mgr1 checks queue
    response = client.get("/manager/requests", headers={"Authorization": f"Bearer {token_mgr1}"})
    assert response.status_code == 200
    data = response.json()
    assert "leaves" in data
    assert "wfh" in data
    assert len(data["leaves"]) == 1
    assert data["leaves"][0]["user_id"] == emp1.id  # Direct report only


def test_employee_calling_manager_route_returns_403(client: TestClient, manager_setup):
    """07: Employees calling any /manager/* route receive 403 Forbidden."""
    emp1 = manager_setup["emp1"]
    token_emp1 = get_token(emp1)

    response = client.get("/manager/requests", headers={"Authorization": f"Bearer {token_emp1}"})
    assert response.status_code == 403


def test_manager_approve_leave_success(client: TestClient, manager_setup):
    """02 & 06: Approving a leave records decided_by, decided_at, and optional comment."""
    mgr1 = manager_setup["mgr1"]
    emp1 = manager_setup["emp1"]
    token_mgr1 = get_token(mgr1)
    token_emp1 = get_token(emp1)

    target_date = (date.today() + timedelta(days=15)).isoformat()

    res_create = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token_emp1}"},
        json={"date": target_date, "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )
    leave_id = res_create.json()["id"]

    res_approve = client.post(
        f"/manager/leaves/{leave_id}/approve",
        headers={"Authorization": f"Bearer {token_mgr1}"},
        json={"comment": "Approved, enjoy!"}
    )
    assert res_approve.status_code == 200
    data = res_approve.json()
    assert data["status"] == "APPROVED"
    assert data["decided_by"] == mgr1.id
    assert data["decided_at"] is not None
    assert data["decision_comment"] == "Approved, enjoy!"


def test_manager_reject_leave_comment_validation(client: TestClient, manager_setup):
    """03: Rejection requires a comment (min 5 characters). Short or missing comments return 422."""
    mgr1 = manager_setup["mgr1"]
    emp1 = manager_setup["emp1"]
    token_mgr1 = get_token(mgr1)
    token_emp1 = get_token(emp1)

    target_date = (date.today() + timedelta(days=18)).isoformat()

    res_create = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token_emp1}"},
        json={"date": target_date, "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )
    leave_id = res_create.json()["id"]

    # Reject without comment -> 422
    res_no_comment = client.post(
        f"/manager/leaves/{leave_id}/reject",
        headers={"Authorization": f"Bearer {token_mgr1}"},
        json={}
    )
    assert res_no_comment.status_code == 422

    # Reject with short comment (< 5 chars) -> 422
    res_short = client.post(
        f"/manager/leaves/{leave_id}/reject",
        headers={"Authorization": f"Bearer {token_mgr1}"},
        json={"comment": "No"}
    )
    assert res_short.status_code == 422

    # Reject with valid comment >= 5 chars -> 200
    res_valid = client.post(
        f"/manager/leaves/{leave_id}/reject",
        headers={"Authorization": f"Bearer {token_mgr1}"},
        json={"comment": "Team critical deliverables pending"}
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["status"] == "REJECTED"
    assert res_valid.json()["decision_comment"] == "Team critical deliverables pending"


def test_manager_cannot_decide_other_teams_request_returns_403(client: TestClient, manager_setup):
    """04: A manager may only decide requests from their own direct reports. Other returns 403."""
    mgr1 = manager_setup["mgr1"]
    emp2 = manager_setup["emp2"]  # Reports to mgr2, NOT mgr1!
    token_mgr1 = get_token(mgr1)
    token_emp2 = get_token(emp2)

    target_date = (date.today() + timedelta(days=22)).isoformat()

    res_create = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token_emp2}"},
        json={"date": target_date, "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )
    leave_id = res_create.json()["id"]

    # mgr1 tries to decide emp2's request -> 403 Forbidden
    response = client.post(
        f"/manager/leaves/{leave_id}/approve",
        headers={"Authorization": f"Bearer {token_mgr1}"}
    )
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


def test_deciding_already_decided_request_returns_409(client: TestClient, manager_setup):
    """05: Only PENDING requests can be decided. Deciding an already decided request returns 409."""
    mgr1 = manager_setup["mgr1"]
    emp1 = manager_setup["emp1"]
    token_mgr1 = get_token(mgr1)
    token_emp1 = get_token(emp1)

    target_date = (date.today() + timedelta(days=25)).isoformat()

    res_create = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token_emp1}"},
        json={"date": target_date, "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )
    leave_id = res_create.json()["id"]

    # First decision: Approve
    res_approve = client.post(
        f"/manager/leaves/{leave_id}/approve",
        headers={"Authorization": f"Bearer {token_mgr1}"}
    )
    assert res_approve.status_code == 200

    # Second decision: Try to Reject -> 409 Conflict
    res_second = client.post(
        f"/manager/leaves/{leave_id}/reject",
        headers={"Authorization": f"Bearer {token_mgr1}"},
        json={"comment": "Changed mind, need you here"}
    )
    assert res_second.status_code == 409
    assert "invalid status transition" in res_second.json()["detail"].lower()


def test_manager_wfh_decision_workflow(client: TestClient, manager_setup):
    """02: Manager can approve and reject WFH requests under /manager/wfh/{id}."""
    mgr1 = manager_setup["mgr1"]
    emp1 = manager_setup["emp1"]
    token_mgr1 = get_token(mgr1)
    token_emp1 = get_token(emp1)

    # Helper date
    today = date.today()
    fri = today + timedelta(days=(4 - today.weekday() + 14))

    # Create WFH
    res_create = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token_emp1}"},
        json={"start_date": fri.isoformat(), "end_date": fri.isoformat()}
    )
    wfh_id = res_create.json()["id"]

    # Approve WFH
    res_approve = client.post(
        f"/manager/wfh/{wfh_id}/approve",
        headers={"Authorization": f"Bearer {token_mgr1}"},
        json={"comment": "Approved WFH"}
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "APPROVED"
    assert res_approve.json()["decided_by"] == mgr1.id
