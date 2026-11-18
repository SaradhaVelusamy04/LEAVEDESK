from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user with email and password to receive a JWT bearer token.",
    responses={
        200: {"description": "Authentication successful, returns JWT bearer token"},
        401: {"description": "Invalid credentials (generic error for both unknown email and incorrect password)"},
        422: {"description": "Validation error in request payload"}
    }
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password."""
    user_repo = UserRepository(db)
    service = AuthService(user_repo)
    return service.authenticate_user(payload.email, payload.password)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current User Profile",
    description="Fetch the authenticated user's profile. Does not expose password hashes.",
    responses={
        200: {"description": "Current user profile retrieved successfully"},
        401: {"description": "Missing, expired, or invalid bearer token"}
    }
)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve logged-in user profile."""
    return AuthService.get_user_profile(current_user)
