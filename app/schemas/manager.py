from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.schemas.leave import LeaveResponse
from app.schemas.wfh import WfhResponse


class DecisionApproveRequest(BaseModel):
    """Payload for approving a request."""
    comment: Optional[str] = None


class DecisionRejectRequest(BaseModel):
    """Payload for rejecting a request (comment minimum 5 characters required)."""
    comment: str = Field(..., min_length=5, description="Mandatory reason for rejection (min 5 characters)")

    @field_validator("comment")
    @classmethod
    def validate_comment_not_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 5:
            raise ValueError("Rejection comment must be at least 5 non-whitespace characters")
        return stripped


class ManagerRequestsResponse(BaseModel):
    """Aggregated review queue containing direct reports' leave and WFH requests."""
    leaves: List[LeaveResponse]
    wfh: List[WfhResponse]
