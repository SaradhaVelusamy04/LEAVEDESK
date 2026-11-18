from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator
from app.domain.rules import calculate_working_days


class WfhCreateRequest(BaseModel):
    """Payload for submitting a Work-From-Home (WFH) request."""
    start_date: date
    end_date: date
    reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_wfh_dates(self):
        # Validate that the span covers between 1 and 2 working days (Monday-Friday)
        calculate_working_days(self.start_date, self.end_date)
        return self


class WfhResponse(BaseModel):
    """Response DTO for Work-From-Home (WFH) requests."""
    id: int
    user_id: int
    start_date: date
    end_date: date
    working_days_count: int
    reason: Optional[str] = None
    status: str
    decided_by: Optional[int] = None
    decided_at: Optional[datetime] = None
    decision_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
