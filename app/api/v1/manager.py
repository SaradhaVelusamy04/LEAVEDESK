from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.repositories.leave_repo import LeaveRepository
from app.repositories.wfh_repo import WfhRepository
from app.services.manager_service import ManagerService
from app.schemas.leave import LeaveResponse
from app.schemas.wfh import WfhResponse
from app.schemas.manager import (
    DecisionApproveRequest,
    DecisionRejectRequest,
    ManagerRequestsResponse
)

router = APIRouter(
    prefix="/manager",
    tags=["Manager Workflow"],
    dependencies=[Depends(require_role("manager"))]
)


def get_manager_service(db: Session = Depends(get_db)) -> ManagerService:
    return ManagerService(
        db=db,
        user_repo=UserRepository(db),
        leave_repo=LeaveRepository(db),
        wfh_repo=WfhRepository(db)
    )


@router.get(
    "/requests",
    response_model=ManagerRequestsResponse,
    status_code=status.HTTP_200_OK,
    summary="Review Direct Reports Requests",
    description="Fetch leave and WFH requests of direct reports. Defaults to status=PENDING.",
    responses={
        200: {"description": "Review queue retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Manager role required"}
    }
)
def get_manager_requests(
    status: Optional[str] = Query("PENDING", description="Filter by status (defaults to PENDING)"),
    employee_id: Optional[int] = Query(None, description="Filter requests for a specific direct report"),
    from_date: Optional[date] = Query(None, description="Filter requests on or after this date"),
    to_date: Optional[date] = Query(None, description="Filter requests on or before this date"),
    current_user: User = Depends(require_role("manager")),
    service: ManagerService = Depends(get_manager_service)
):
    """Retrieve review queue of direct reports."""
    return service.get_review_queue(
        manager=current_user,
        status=status,
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date
    )


@router.post(
    "/leaves/{leave_id}/approve",
    response_model=LeaveResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve Leave Request",
    description="Approve a pending leave request from a direct report. Accepts an optional comment.",
    responses={
        200: {"description": "Leave request approved successfully"},
        403: {"description": "Manager is not authorized to decide requests outside their team"},
        404: {"description": "Leave request not found"},
        409: {"description": "Request is not in PENDING status"}
    }
)
def approve_leave(
    leave_id: int,
    payload: Optional[DecisionApproveRequest] = None,
    current_user: User = Depends(require_role("manager")),
    service: ManagerService = Depends(get_manager_service)
):
    """Approve a leave request."""
    comment = payload.comment if payload else None
    return service.decide_leave(
        manager=current_user,
        leave_id=leave_id,
        approve=True,
        comment=comment
    )


@router.post(
    "/leaves/{leave_id}/reject",
    response_model=LeaveResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject Leave Request",
    description="Reject a pending leave request from a direct report. Mandatory comment (min 5 chars).",
    responses={
        200: {"description": "Leave request rejected successfully"},
        403: {"description": "Manager is not authorized to decide requests outside their team"},
        404: {"description": "Leave request not found"},
        409: {"description": "Request is not in PENDING status"},
        422: {"description": "Rejection comment missing or under 5 characters"}
    }
)
def reject_leave(
    leave_id: int,
    payload: DecisionRejectRequest,
    current_user: User = Depends(require_role("manager")),
    service: ManagerService = Depends(get_manager_service)
):
    """Reject a leave request."""
    return service.decide_leave(
        manager=current_user,
        leave_id=leave_id,
        approve=False,
        comment=payload.comment
    )


@router.post(
    "/wfh/{wfh_id}/approve",
    response_model=WfhResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve WFH Request",
    description="Approve a pending WFH request from a direct report. Accepts an optional comment.",
    responses={
        200: {"description": "WFH request approved successfully"},
        403: {"description": "Manager is not authorized to decide requests outside their team"},
        404: {"description": "WFH request not found"},
        409: {"description": "Request is not in PENDING status"}
    }
)
def approve_wfh(
    wfh_id: int,
    payload: Optional[DecisionApproveRequest] = None,
    current_user: User = Depends(require_role("manager")),
    service: ManagerService = Depends(get_manager_service)
):
    """Approve a WFH request."""
    comment = payload.comment if payload else None
    return service.decide_wfh(
        manager=current_user,
        wfh_id=wfh_id,
        approve=True,
        comment=comment
    )


@router.post(
    "/wfh/{wfh_id}/reject",
    response_model=WfhResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject WFH Request",
    description="Reject a pending WFH request from a direct report. Mandatory comment (min 5 chars).",
    responses={
        200: {"description": "WFH request rejected successfully"},
        403: {"description": "Manager is not authorized to decide requests outside their team"},
        404: {"description": "WFH request not found"},
        409: {"description": "Request is not in PENDING status"},
        422: {"description": "Rejection comment missing or under 5 characters"}
    }
)
def reject_wfh(
    wfh_id: int,
    payload: DecisionRejectRequest,
    current_user: User = Depends(require_role("manager")),
    service: ManagerService = Depends(get_manager_service)
):
    """Reject a WFH request."""
    return service.decide_wfh(
        manager=current_user,
        wfh_id=wfh_id,
        approve=False,
        comment=payload.comment
    )
