from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.domain.enums import RoleEnum
from app.core.security import get_password_hash, create_access_token
from app.api.deps import require_role
from fastapi import APIRouter, Depends

# Create a dummy manager-only test endpoint to verify require_role("manager")
dummy_router = APIRouter(prefix="/role-check")


@dummy_router.get("/manager-only")
def manager_only_endpoint(current_user: User = Depends(require_role("manager"))):
    return {"message": "Welcome Manager", "user_id": current_user.id}


app.include_router(dummy_router)


@pytest.fixture
def seeded_users(db_session: Session):
    """Seed test users directly into test database session."""
    manager = User(
        name="Priya Manager",
        email="priya.manager@leavedesk.test",
        role=RoleEnum.MANAGER.value,
        hashed_password=get_password_hash("Manager@123"),
        reports_to_id=None
    )
    db_session.add(manager)
    db_session.commit()
    db_session.refresh(manager)

    employee = User(
        name="Arjun Employee",
        email="arjun@leavedesk.test",
        role=RoleEnum.EMPLOYEE.value,
        hashed_password=get_password_hash("Employee@123"),
        reports_to_id=manager.id
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return {"manager": manager, "employee": employee}


def test_auth_login_success(client: TestClient, seeded_users):
    """01: POST /auth/login accepts email and password and returns JWT with token_type: bearer."""
    response = client.post(
        "/auth/login",
        json={"email": "arjun@leavedesk.test", "password": "Employee@123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_auth_login_generic_401_on_wrong_password_and_unknown_email(client: TestClient, seeded_users):
    """03: Wrong email or wrong password returns 401 with the exact same generic message."""
    # Test wrong password
    resp_wrong_pw = client.post(
        "/auth/login",
        json={"email": "arjun@leavedesk.test", "password": "WrongPassword!"}
    )
    assert resp_wrong_pw.status_code == 401
    msg_wrong_pw = resp_wrong_pw.json()["detail"]

    # Test unknown email
    resp_unknown_email = client.post(
        "/auth/login",
        json={"email": "nonexistent@leavedesk.test", "password": "Employee@123"}
    )
    assert resp_unknown_email.status_code == 401
    msg_unknown_email = resp_unknown_email.json()["detail"]

    # Must be identical generic error message
    assert msg_wrong_pw == msg_unknown_email
    assert "invalid" in msg_wrong_pw.lower()


def test_auth_token_expired(client: TestClient, seeded_users):
    """04: Expired token returns 401."""
    employee = seeded_users["employee"]
    # Create an expired token (negative delta)
    expired_token = create_access_token(
        data={"sub": str(employee.id), "role": employee.role},
        expires_delta=timedelta(minutes=-10)
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_auth_token_tampered(client: TestClient):
    """04: Tampered/invalid token returns 401."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.tampered.token"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_auth_get_me_success_and_no_password_exposed(client: TestClient, seeded_users):
    """05: GET /auth/me returns logged-in user id, name, email, role, manager_id - never password hash."""
    employee = seeded_users["employee"]
    token = create_access_token(data={"sub": str(employee.id), "role": employee.role})

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == employee.id
    assert data["name"] == "Arjun Employee"
    assert data["email"] == "arjun@leavedesk.test"
    assert data["role"] == "employee"
    assert data["manager_id"] == seeded_users["manager"].id

    # Verify password hash is never exposed in response
    assert "password" not in data
    assert "hashed_password" not in data


def test_role_enforcement_employee_cannot_access_manager_route(client: TestClient, seeded_users):
    """06: An employee calling a manager-only route receives 403 Forbidden."""
    employee = seeded_users["employee"]
    token = create_access_token(data={"sub": str(employee.id), "role": employee.role})

    response = client.get(
        "/role-check/manager-only",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "forbidden" in response.json()["detail"].lower()


def test_role_enforcement_manager_can_access_manager_route(client: TestClient, seeded_users):
    """06: A manager calling a manager-only route succeeds."""
    manager = seeded_users["manager"]
    token = create_access_token(data={"sub": str(manager.id), "role": manager.role})

    response = client.get(
        "/role-check/manager-only",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome Manager"


def test_seed_script_execution():
    """Verify seed script runs idempotently without error."""
    from seed import seed_database
    seed_database()
    # Running a second time should also be completely idempotent
    seed_database()
