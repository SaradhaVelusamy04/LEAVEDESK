from datetime import date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.models.wfh import WfhRequest
from app.repositories.wfh_repo import WfhRepository
from app.repositories.leave_repo import LeaveRepository
from app.schemas.wfh import WfhCreateRequest, WfhResponse
from app.domain.enums import DurationTypeEnum, RequestStatusEnum
from app.domain.rules import calculate_working_days
from app.domain.state_machine import RequestStateMachine
from app.core.exceptions import ConflictException, ResourceNotFoundException


class WfhService:
    """Application service orchestrating Work-From-Home (WFH) workflows."""

    def __init__(self, db: Session, wfh_repo: WfhRepository, leave_repo: LeaveRepository):
        self.db = db
        self.wfh_repo = wfh_repo
        self.leave_repo = leave_repo

    def create_wfh(self, user: User, data: WfhCreateRequest) -> WfhResponse:
        """Create a new WFH request with concurrency-safe overlap checking."""
        # Acquire row-level pessimistic lock on user record to serialize concurrent submissions
        stmt = select(User).where(User.id == user.id).with_for_update()
        self.db.scalars(stmt).first()

        working_days = calculate_working_days(data.start_date, data.end_date)

        # 1. Check overlap with other active WFH requests for this user
        overlapping_wfh = self.wfh_repo.get_active_overlapping_wfh(
            user_id=user.id,
            start_date=data.start_date,
            end_date=data.end_date
        )
        if overlapping_wfh:
            raise ConflictException(
                detail=f"An active Work-From-Home request already overlaps the requested range ({data.start_date} to {data.end_date})."
            )

        # 2. Check overlap with active FULL_DAY leaves
        active_leaves = self.leave_repo.get_active_leaves_in_date_range(
            user_id=user.id,
            start_date=data.start_date,
            end_date=data.end_date
        )
        for leave in active_leaves:
            if leave.duration_type == DurationTypeEnum.FULL_DAY.value:
                raise ConflictException(
                    detail=f"WFH request cannot overlap an active FULL_DAY leave on {leave.date}."
                )

        wfh = self.wfh_repo.create(
            user_id=user.id,
            start_date=data.start_date,
            end_date=data.end_date,
            working_days_count=working_days,
            reason=data.reason
        )

        return WfhResponse.model_validate(wfh)

    def list_my_wfh(
        self,
        user: User,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[WfhResponse]:
        """List current user's WFH requests, newest first, with optional filters."""
        wfh_list = self.wfh_repo.get_user_wfh(
            user_id=user.id,
            status=status,
            from_date=from_date,
            to_date=to_date
        )
        return [WfhResponse.model_validate(w) for w in wfh_list]

    def cancel_wfh(self, current_user: User, wfh_id: int) -> WfhResponse:
        """Cancel a pending WFH request owned by current user."""
        wfh = self.wfh_repo.get_by_id(wfh_id)
        if not wfh:
            raise ResourceNotFoundException(detail="Work-From-Home request not found")

        # Hide existence if not owned by caller to prevent resource enumeration
        if wfh.user_id != current_user.id:
            raise ResourceNotFoundException(detail="Work-From-Home request not found")

        # Validate transition using centralized State Machine
        RequestStateMachine.validate_transition(
            current_status=RequestStatusEnum(wfh.status),
            target_status=RequestStatusEnum.CANCELLED
        )

        wfh.status = RequestStatusEnum.CANCELLED.value
        updated_wfh = self.wfh_repo.update(wfh)
        return WfhResponse.model_validate(updated_wfh)
