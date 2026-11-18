from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.leave_repo import LeaveRepository
from app.repositories.wfh_repo import WfhRepository
from app.services.leave_service import LeaveService
from app.schemas.leave import LeaveCreateRequest, LeaveResponse

router = APIRouter(prefix="/leaves", tags=["Leaves"])


@router.post(
    "",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Leave Request",
    description="Submit a new leave request with duration validation and conflict checking. Initial status is PENDING.",
    responses={
        201: {"description": "Leave request created successfully"},
        401: {"description": "Authentication required"},
        409: {"description": "Conflict with an existing active leave or WFH request"},
        422: {"description": "Validation error in duration fields or combinations"}
    }
)
def create_leave(
    payload: LeaveCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a new leave request."""
    service = LeaveService(db, LeaveRepository(db), WfhRepository(db))
    return service.create_leave(current_user, payload)


@router.get(
    "/me",
    response_model=List[LeaveResponse],
    status_code=status.HTTP_200_OK,
    summary="List My Leave Requests",
    description="Retrieve all leave requests belonging to the authenticated caller, newest first.",
    responses={
        200: {"description": "List of user's leave requests"},
        401: {"description": "Authentication required"}
    }
)
def list_my_leaves(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED, CANCELLED)"),
    from_date: Optional[date] = Query(None, description="Filter requests on or after this date"),
    to_date: Optional[date] = Query(None, description="Filter requests on or before this date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve personal leave history."""
    service = LeaveService(db, LeaveRepository(db), WfhRepository(db))
    return service.list_my_leaves(current_user, status=status, from_date=from_date, to_date=to_date)


@router.post(
    "/{leave_id}/cancel",
    response_model=LeaveResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Pending Leave Request",
    description="Cancel a PENDING leave request owned by the authenticated caller.",
    responses={
        200: {"description": "Leave request cancelled successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Request not found or not owned by caller"},
        409: {"description": "Request is not in PENDING status"}
    }
)
def cancel_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending leave request."""
    service = LeaveService(db, LeaveRepository(db), WfhRepository(db))
    return service.cancel_leave(current_user, leave_id)
