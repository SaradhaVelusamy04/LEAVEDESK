from datetime import datetime, timezone, date
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.repositories.leave_repo import LeaveRepository
from app.repositories.wfh_repo import WfhRepository
from app.schemas.leave import LeaveResponse
from app.schemas.wfh import WfhResponse
from app.schemas.manager import ManagerRequestsResponse
from app.domain.enums import RequestStatusEnum
from app.domain.state_machine import RequestStateMachine
from app.core.exceptions import (
    ResourceNotFoundException,
    AuthorizationException,
    ValidationException,
    ConflictException
)


class ManagerService:
    """Application service orchestrating manager review and decision workflows."""

    def __init__(
        self,
        db: Session,
        user_repo: UserRepository,
        leave_repo: LeaveRepository,
        wfh_repo: WfhRepository
    ):
        self.db = db
        self.user_repo = user_repo
        self.leave_repo = leave_repo
        self.wfh_repo = wfh_repo

    def get_review_queue(
        self,
        manager: User,
        status: Optional[str] = "PENDING",
        employee_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> ManagerRequestsResponse:
        """Fetch leave and WFH requests submitted by the manager's direct reports."""
        direct_reports = self.user_repo.get_direct_reports(manager.id)
        direct_report_ids = [u.id for u in direct_reports]

        if not direct_report_ids:
            return ManagerRequestsResponse(leaves=[], wfh=[])

        team_leaves = self.leave_repo.get_team_leaves(
            direct_report_ids=direct_report_ids,
            status=status,
            employee_id=employee_id,
            from_date=from_date,
            to_date=to_date
        )

        team_wfh = self.wfh_repo.get_team_wfh(
            direct_report_ids=direct_report_ids,
            status=status,
            employee_id=employee_id,
            from_date=from_date,
            to_date=to_date
        )

        return ManagerRequestsResponse(
            leaves=[LeaveResponse.model_validate(l) for l in team_leaves],
            wfh=[WfhResponse.model_validate(w) for w in team_wfh]
        )

    def decide_leave(
        self,
        manager: User,
        leave_id: int,
        approve: bool,
        comment: Optional[str] = None
    ) -> LeaveResponse:
        """Approve or reject an employee's leave request."""
        leave = self.leave_repo.get_by_id(leave_id)
        if not leave:
            raise ResourceNotFoundException(detail="Leave request not found")

        # Verify direct report relationship
        requester = self.user_repo.get_by_id(leave.user_id)
        if not requester or requester.reports_to_id != manager.id:
            raise AuthorizationException(
                detail="You are not authorized to decide requests for employees outside your team"
            )

        target_status = RequestStatusEnum.APPROVED if approve else RequestStatusEnum.REJECTED

        # Centralized State Machine validation
        RequestStateMachine.validate_transition(
            current_status=RequestStatusEnum(leave.status),
            target_status=target_status
        )

        # Validate rejection comment
        if not approve:
            if not comment or len(comment.strip()) < 5:
                raise ValidationException(detail="Rejection requires a comment of at least 5 characters")

        # Record decision audit trail
        leave.status = target_status.value
        leave.decided_by = manager.id
        leave.decided_at = datetime.now(timezone.utc)
        leave.decision_comment = comment.strip() if comment else None

        updated_leave = self.leave_repo.update(leave)
        return LeaveResponse.model_validate(updated_leave)

    def decide_wfh(
        self,
        manager: User,
        wfh_id: int,
        approve: bool,
        comment: Optional[str] = None
    ) -> WfhResponse:
        """Approve or reject an employee's WFH request."""
        wfh = self.wfh_repo.get_by_id(wfh_id)
        if not wfh:
            raise ResourceNotFoundException(detail="Work-From-Home request not found")

        # Verify direct report relationship
        requester = self.user_repo.get_by_id(wfh.user_id)
        if not requester or requester.reports_to_id != manager.id:
            raise AuthorizationException(
                detail="You are not authorized to decide requests for employees outside your team"
            )

        target_status = RequestStatusEnum.APPROVED if approve else RequestStatusEnum.REJECTED

        # Centralized State Machine validation
        RequestStateMachine.validate_transition(
            current_status=RequestStatusEnum(wfh.status),
            target_status=target_status
        )

        # Validate rejection comment
        if not approve:
            if not comment or len(comment.strip()) < 5:
                raise ValidationException(detail="Rejection requires a comment of at least 5 characters")

        # Record decision audit trail
        wfh.status = target_status.value
        wfh.decided_by = manager.id
        wfh.decided_at = datetime.now(timezone.utc)
        wfh.decision_comment = comment.strip() if comment else None

        updated_wfh = self.wfh_repo.update(wfh)
        return WfhResponse.model_validate(updated_wfh)
