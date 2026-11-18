from datetime import date, datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, model_validator, field_validator
from app.domain.enums import LeaveTypeEnum, DurationTypeEnum, HalfEnum, RequestStatusEnum
from app.domain.rules import validate_and_calculate_leave_days


class LeaveCreateRequest(BaseModel):
    """Payload for submitting a leave request."""
    date: date
    leave_type: LeaveTypeEnum
    duration_type: DurationTypeEnum
    half: Optional[HalfEnum] = None
    hours: Optional[Any] = None
    reason: Optional[str] = None

    @field_validator("hours")
    @classmethod
    def validate_hours_field(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        # Reject booleans or float or string like "90 minutes"
        if isinstance(v, bool):
            raise ValueError("hours must be an integer")
        if isinstance(v, float) and not v.is_integer():
            raise ValueError("hours must be an integer from 1 to 3, fractional values are not accepted")
        try:
            int_val = int(v)
            if float(v) != int_val:
                raise ValueError("hours must be a whole number")
        except (ValueError, TypeError):
            raise ValueError("hours must be an integer from 1 to 3")

        if int_val not in (1, 2, 3):
            raise ValueError("hours must be an integer from 1 to 3")
        return int_val

    @model_validator(mode="after")
    def validate_duration_fields(self):
        # Validate combinations using domain rule
        validate_and_calculate_leave_days(
            duration_type=self.duration_type,
            half=self.half,
            hours=self.hours
        )
        return self


class LeaveResponse(BaseModel):
    """Response DTO for leave requests."""
    id: int
    user_id: int
    date: date
    leave_type: str
    duration_type: str
    half: Optional[str] = None
    hours: Optional[int] = None
    days_counted: float
    reason: Optional[str] = None
    status: str
    decided_by: Optional[int] = None
    decided_at: Optional[datetime] = None
    decision_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
