from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.leave import LeaveRequest
from app.domain.enums import RoleEnum, RequestStatusEnum
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def test_users(db_session: Session):
    """Seed manager and two test employees."""
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


def test_create_leave_full_day(client: TestClient, test_users):
    """01 & 03: FULL_DAY leave creation with days_counted=1.0 and initial status PENDING."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)
    target_date = (date.today() + timedelta(days=10)).isoformat()

    response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date": target_date,
            "leave_type": "CASUAL",
            "duration_type": "FULL_DAY",
            "reason": "Personal work"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["duration_type"] == "FULL_DAY"
    assert data["days_counted"] == 1.0
    assert data["half"] is None
    assert data["hours"] is None
    assert data["reason"] == "Personal work"


def test_create_leave_half_day_and_coexistence(client: TestClient, test_users):
    """03 & 04: HALF_DAY FIRST_HALF and SECOND_HALF can coexist on the same date."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)
    target_date = (date.today() + timedelta(days=12)).isoformat()

    # Create FIRST_HALF
    res1 = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date": target_date,
            "leave_type": "SICK",
            "duration_type": "HALF_DAY",
            "half": "FIRST_HALF"
        }
    )
    assert res1.status_code == 201
    assert res1.json()["days_counted"] == 0.5
    assert res1.json()["half"] == "FIRST_HALF"

    # Create SECOND_HALF on same date - should succeed
    res2 = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date": target_date,
            "leave_type": "EARNED",
            "duration_type": "HALF_DAY",
            "half": "SECOND_HALF"
        }
    )
    assert res2.status_code == 201
    assert res2.json()["days_counted"] == 0.5
    assert res2.json()["half"] == "SECOND_HALF"

    # Creating another FIRST_HALF on same date - must return 409 Conflict
    res3 = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date": target_date,
            "leave_type": "CASUAL",
            "duration_type": "HALF_DAY",
            "half": "FIRST_HALF"
        }
    )
    assert res3.status_code == 409
    assert "already exists" in res3.json()["detail"].lower()


def test_create_leave_hours_duration(client: TestClient, test_users):
    """02: HOURS duration accepted for integers 1, 2, 3 and counted as hours / 8."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)
    target_date = (date.today() + timedelta(days=15)).isoformat()

    response = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date": target_date,
            "leave_type": "CASUAL",
            "duration_type": "HOURS",
            "hours": 2
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["duration_type"] == "HOURS"
    assert data["hours"] == 2
    assert data["days_counted"] == 0.25  # 2 / 8


def test_rejected_hours_values(client: TestClient, test_users):
    """02: Hours outside 1-3, decimals, 0, or string like '90 minutes' rejected with 422."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)
    target_date = (date.today() + timedelta(days=20)).isoformat()

    invalid_hours = [0, 4, 1.5, "90 minutes", -1]
    for h in invalid_hours:
        res = client.post(
            "/leaves",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "date": target_date,
                "leave_type": "CASUAL",
                "duration_type": "HOURS",
                "hours": h
            }
        )
        assert res.status_code == 422, f"Expected 422 for hours={h}, got {res.status_code}"


def test_mismatched_duration_fields_rejected_422(client: TestClient, test_users):
    """03: half missing for HALF_DAY, or extra fields on FULL_DAY/HOURS rejected with 422."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)
    target_date = (date.today() + timedelta(days=25)).isoformat()

    # HALF_DAY missing half
    res1 = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": target_date, "leave_type": "SICK", "duration_type": "HALF_DAY"}
    )
    assert res1.status_code == 422

    # FULL_DAY with half
    res2 = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": target_date, "leave_type": "SICK", "duration_type": "FULL_DAY", "half": "FIRST_HALF"}
    )
    assert res2.status_code == 422

    # FULL_DAY with hours
    res3 = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": target_date, "leave_type": "SICK", "duration_type": "FULL_DAY", "hours": 2}
    )
    assert res3.status_code == 422


def test_full_day_overlap_conflict(client: TestClient, test_users):
    """04: FULL_DAY blocks any other leave request on that day with 409 Conflict."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)
    target_date = (date.today() + timedelta(days=30)).isoformat()

    # Create FULL_DAY
    res1 = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": target_date, "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )
    assert res1.status_code == 201

    # Attempt another leave on same date
    res2 = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": target_date, "leave_type": "SICK", "duration_type": "HALF_DAY", "half": "FIRST_HALF"}
    )
    assert res2.status_code == 409
    assert "conflict" in res2.json()["detail"].lower() or "active full_day" in res2.json()["detail"].lower()


def test_list_my_leaves_and_filters(client: TestClient, test_users):
    """07: GET /leaves/me returns caller's requests, newest first, with optional filters."""
    emp1 = test_users["emp1"]
    token = get_token(emp1)
    base_date = date.today() + timedelta(days=40)

    # Submit 2 leaves
    client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": base_date.isoformat(), "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )
    client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": (base_date + timedelta(days=2)).isoformat(), "leave_type": "SICK", "duration_type": "FULL_DAY"}
    )

    response = client.get("/leaves/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    leaves = response.json()
    assert len(leaves) >= 2
    # Verify newest first
    assert leaves[0]["created_at"] >= leaves[1]["created_at"]

    # Filter by status
    res_filtered = client.get("/leaves/me?status=PENDING", headers={"Authorization": f"Bearer {token}"})
    assert res_filtered.status_code == 200
    assert all(l["status"] == "PENDING" for l in res_filtered.json())


def test_cancel_leave_success_and_restrictions(client: TestClient, test_users):
    """08 & 09: Only owner can cancel, only PENDING; non-owner returns 404; non-pending returns 409."""
    emp1 = test_users["emp1"]
    emp2 = test_users["emp2"]
    token_emp1 = get_token(emp1)
    token_emp2 = get_token(emp2)
    target_date = (date.today() + timedelta(days=50)).isoformat()

    # Emp1 creates leave
    res = client.post(
        "/leaves",
        headers={"Authorization": f"Bearer {token_emp1}"},
        json={"date": target_date, "leave_type": "CASUAL", "duration_type": "FULL_DAY"}
    )
    leave_id = res.json()["id"]

    # Emp2 tries to cancel Emp1's leave -> 404 (isolation)
    res_unauthorized = client.post(
        f"/leaves/{leave_id}/cancel",
        headers={"Authorization": f"Bearer {token_emp2}"}
    )
    assert res_unauthorized.status_code == 404

    # Emp1 cancels own leave -> 200, status CANCELLED
    res_cancel = client.post(
        f"/leaves/{leave_id}/cancel",
        headers={"Authorization": f"Bearer {token_emp1}"}
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"

    # Cancelling again -> 409 Conflict
    res_cancel_again = client.post(
        f"/leaves/{leave_id}/cancel",
        headers={"Authorization": f"Bearer {token_emp1}"}
    )
    assert res_cancel_again.status_code == 409
