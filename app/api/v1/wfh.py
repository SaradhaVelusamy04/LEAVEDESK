from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.wfh_repo import WfhRepository
from app.repositories.leave_repo import LeaveRepository
from app.services.wfh_service import WfhService
from app.schemas.wfh import WfhCreateRequest, WfhResponse

router = APIRouter(prefix="/wfh", tags=["Work From Home"])


@router.post(
    "",
    response_model=WfhResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create WFH Request",
    description="Submit a new Work-From-Home request (inclusive, max 2 working days). Initial status is PENDING.",
    responses={
        201: {"description": "WFH request created successfully"},
        401: {"description": "Authentication required"},
        409: {"description": "Conflict with an active WFH request or FULL_DAY leave"},
        422: {"description": "Validation error (invalid date range or exceeding 2 working days)"}
    }
)
def create_wfh(
    payload: WfhCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a new WFH request."""
    service = WfhService(db, WfhRepository(db), LeaveRepository(db))
    return service.create_wfh(current_user, payload)


@router.get(
    "/me",
    response_model=List[WfhResponse],
    status_code=status.HTTP_200_OK,
    summary="List My WFH Requests",
    description="Retrieve all WFH requests belonging to the authenticated caller, newest first.",
    responses={
        200: {"description": "List of user's WFH requests"},
        401: {"description": "Authentication required"}
    }
)
def list_my_wfh(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED, CANCELLED)"),
    from_date: Optional[date] = Query(None, description="Filter requests overlapping on or after this date"),
    to_date: Optional[date] = Query(None, description="Filter requests overlapping on or before this date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve personal WFH history."""
    service = WfhService(db, WfhRepository(db), LeaveRepository(db))
    return service.list_my_wfh(current_user, status=status, from_date=from_date, to_date=to_date)


@router.post(
    "/{wfh_id}/cancel",
    response_model=WfhResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Pending WFH Request",
    description="Cancel a PENDING WFH request owned by the authenticated caller.",
    responses={
        200: {"description": "WFH request cancelled successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Request not found or not owned by caller"},
        409: {"description": "Request is not in PENDING status"}
    }
)
def cancel_wfh(
    wfh_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending WFH request."""
    service = WfhService(db, WfhRepository(db), LeaveRepository(db))
    return service.cancel_wfh(current_user, wfh_id)
