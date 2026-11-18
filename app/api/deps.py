from typing import Generator, Callable
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.models.user import User
from app.repositories.user_repo import UserRepository

# HTTPBearer extracts 'Bearer <token>' from Authorization header
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency that authenticates JWT access tokens and returns current user."""
    if not credentials or not credentials.credentials:
        raise AuthenticationException(detail="Authentication credentials were not provided")

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException(detail="Invalid token payload")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise AuthenticationException(detail="Invalid token subject")

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise AuthenticationException(detail="User account not found")

    return user


def require_role(required_role: str) -> Callable:
    """Factory dependency enforcing specific user roles."""
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise AuthorizationException(
                detail=f"Access forbidden: requires '{required_role}' role"
            )
        return current_user

    return role_dependency
