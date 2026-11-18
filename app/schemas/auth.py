import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class LoginRequest(BaseModel):
    """Payload for user login."""
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        # Allows valid emails including .test, .internal, etc.
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format")
        return v


class TokenResponse(BaseModel):
    """JWT response structure."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user profile information."""
    id: int
    name: str
    email: str
    role: str
    manager_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
