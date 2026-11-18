from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from app.domain.enums import RoleEnum


@pytest.fixture
def test_users(db_session: Session):
    manager = User(
        name="Priya Manager",
        email="priya.manager@leavedesk.test",
        role=RoleEnum.MANAGER.value,
        hashed_password=get_password_hash("Manager@123")
    )
    db_session.add(manager)
    db_session.commit()
    db_session.refresh(manager)

    emp1 = User(
        name="Arjun Employee",
        email="arjun@leavedesk.test",
        role=RoleEnum.EMPLOYEE.value,
        hashed_password=get_password_hash("Employee@123"),
        reports_to_id=manager.id
    )
    emp2 = User(
        name="Meera Employee",
        email="meera@leavedesk.test",
        role=RoleEnum.EMPLOYEE.value,
        hashed_password=get_password_hash("Employee@123"),
        reports_to_id=manager.id
    )
    db_session.add_all([emp1, emp2])
    db_session.commit()
    db_session.refresh(emp1)
    db_session.refresh(emp2)

    return {"manager": manager, "emp1": emp1, "emp2": emp2}


def get_token(user: User) -> str:
    return create_access_token(data={"sub": str(user.id), "role": user.role})


def get_next_weekday(target_weekday: int, weeks_ahead: int = 1) -> date:
    """Find the next specific weekday (0=Mon, 4=Fri, 5=Sat, 6=Sun)."""
    today = date.today()
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead + (weeks_ahead * 7))


def test_create_wfh_success(client: TestClient, test_users):
    """05: POST /wfh creates a WFH request with status PENDING and max 2 working days."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)

    mon = get_next_weekday(0, weeks_ahead=1)  # Next Monday
    tue = mon + timedelta(days=1)            # Next Tuesday (2 working days)

    response = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_date": mon.isoformat(),
            "end_date": tue.isoformat(),
            "reason": "Home office setup"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["working_days_count"] == 2
    assert data["start_date"] == mon.isoformat()
    assert data["end_date"] == tue.isoformat()


def test_create_wfh_friday_to_monday(client: TestClient, test_users):
    """05: Friday to Monday inclusive spans exactly 2 working days (Friday + Monday), valid."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)

    fri = get_next_weekday(4, weeks_ahead=2)  # Friday
    mon = fri + timedelta(days=3)             # Monday

    response = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_date": fri.isoformat(),
            "end_date": mon.isoformat(),
            "reason": "Long weekend work"
        }
    )
    assert response.status_code == 201
    assert response.json()["working_days_count"] == 2


def test_wfh_exceeding_two_working_days_rejected_422(client: TestClient, test_users):
    """05: WFH exceeding 2 working days (e.g. Monday to Wednesday = 3 working days) returns 422."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)

    mon = get_next_weekday(0, weeks_ahead=3)
    wed = mon + timedelta(days=2)  # Mon, Tue, Wed = 3 working days

    response = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_date": mon.isoformat(),
            "end_date": wed.isoformat()
        }
    )
    assert response.status_code == 422
    assert "cannot exceed 2 working days" in response.json()["detail"].lower()


def test_wfh_weekend_only_rejected_422(client: TestClient, test_users):
    """05: Request spanning only Saturday to Sunday has 0 working days, returns 422."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)

    sat = get_next_weekday(5, weeks_ahead=1)
    sun = sat + timedelta(days=1)

    response = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_date": sat.isoformat(),
            "end_date": sun.isoformat()
        }
    )
    assert response.status_code == 422
    assert "does not contain any working days" in response.json()["detail"].lower()


def test_wfh_overlap_with_active_wfh_returns_409(client: TestClient, test_users):
    """06: A WFH request cannot overlap another active WFH request for the same user (409)."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)

    mon = get_next_weekday(0, weeks_ahead=4)
    tue = mon + timedelta(days=1)

    # First request
    res1 = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token}"},
        json={"start_date": mon.isoformat(), "end_date": tue.isoformat()}
    )
    assert res1.status_code == 201

    # Overlapping request on Tuesday
    res2 = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token}"},
        json={"start_date": tue.isoformat(), "end_date": tue.isoformat()}
    )
    assert res2.status_code == 409
    assert "already overlaps" in res2.json()["detail"].lower()


def test_wfh_overlap_with_full_day_leave_returns_409(client: TestClient, test_users):
    """06: A WFH request cannot overlap a FULL_DAY leave (409)."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)

    thu = get_next_weekday(3, weeks_ahead=5)

    # First create a FULL_DAY leave on Thursday
    res_leave = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": thu.isoformat(), "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )
    assert res_leave.status_code == 201

    # Attempt to create WFH covering Thursday
    res_wfh = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token}"},
        json={"start_date": thu.isoformat(), "end_date": thu.isoformat()}
    )
    assert res_wfh.status_code == 409
    assert "cannot overlap" in res_wfh.json()["detail"].lower()


def test_list_and_cancel_wfh(client: TestClient, test_users):
    """07, 08, 09: List WFH, cancel pending WFH, 404 for non-owner, 409 for non-pending."""
    emp1 = test_users["emp1"]
    emp2 = test_users["emp2"]
    token_emp1 = get_token(emp1)
    token_emp2 = get_token(emp2)

    fri = get_next_weekday(4, weeks_ahead=6)

    # Emp1 submits WFH
    res_create = client.post(
        "/wfh",
        headers={"Authorization": f"Bearer {token_emp1}"},
        json={"start_date": fri.isoformat(), "end_date": fri.isoformat()}
    )
    wfh_id = res_create.json()["id"]

    # Verify listing
    res_list = client.get("/wfh/me", headers={"Authorization": f"Bearer {token_emp1}"})
    assert res_list.status_code == 200
    assert any(w["id"] == wfh_id for w in res_list.json())

    # Emp2 attempts cancel -> 404
    res_unauthorized = client.post(
        f"/wfh/{wfh_id}/cancel",
        headers={"Authorization": f"Bearer {token_emp2}"}
    )
    assert res_unauthorized.status_code == 404

    # Emp1 cancels -> 200
    res_cancel = client.post(
        f"/wfh/{wfh_id}/cancel",
        headers={"Authorization": f"Bearer {token_emp1}"}
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"

    # Cancelling again -> 409
    res_cancel_again = client.post(
        f"/wfh/{wfh_id}/cancel",
        headers={"Authorization": f"Bearer {token_emp1}"}
    )
    assert res_cancel_again.status_code == 409
