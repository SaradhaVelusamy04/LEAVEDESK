from app.repositories.user_repo import UserRepository
from app.core.security import verify_password, create_access_token
from app.core.exceptions import AuthenticationException
from app.schemas.auth import TokenResponse, UserResponse
from app.models.user import User


class AuthService:
    """Application service orchestrating authentication and user identity."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, email: str, password: str) -> TokenResponse:
        """Authenticate user credentials and generate JWT access token."""
        # Standard generic message for both wrong email and wrong password
        generic_error = "Invalid email or password"
        
        user = self.user_repo.get_by_email(email)
        if not user:
            raise AuthenticationException(detail=generic_error)

        if not verify_password(password, user.hashed_password):
            raise AuthenticationException(detail=generic_error)

        # Generate JWT access token with user.id as subject
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return TokenResponse(access_token=token, token_type="bearer")

    @staticmethod
    def get_user_profile(user: User) -> UserResponse:
        """Map user entity to clean public profile DTO."""
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            manager_id=user.reports_to_id
        )
