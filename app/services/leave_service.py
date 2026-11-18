from datetime import date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.models.leave import LeaveRequest
from app.repositories.leave_repo import LeaveRepository
from app.repositories.wfh_repo import WfhRepository
from app.schemas.leave import LeaveCreateRequest, LeaveResponse
from app.domain.enums import DurationTypeEnum, HalfEnum, RequestStatusEnum
from app.domain.rules import validate_and_calculate_leave_days
from app.domain.state_machine import RequestStateMachine
from app.core.exceptions import ConflictException, ResourceNotFoundException


class LeaveService:
    """Application service orchestrating Leave request workflows."""

    def __init__(self, db: Session, leave_repo: LeaveRepository, wfh_repo: WfhRepository):
        self.db = db
        self.leave_repo = leave_repo
        self.wfh_repo = wfh_repo

    def create_leave(self, user: User, data: LeaveCreateRequest) -> LeaveResponse:
        """Create a new leave request with concurrency-safe overlap checking."""
        # Acquire row-level pessimistic lock on user record to serialize concurrent submissions
        stmt = select(User).where(User.id == user.id).with_for_update()
        self.db.scalars(stmt).first()

        days_counted = validate_and_calculate_leave_days(
            duration_type=data.duration_type,
            half=data.half,
            hours=data.hours
        )

        target_date = data.date
        existing_leaves = self.leave_repo.get_active_leaves_on_date(user.id, target_date)

        # 1. Overlap checks against existing active leaves on target_date
        if existing_leaves:
            # Any existing FULL_DAY blocks everything
            for ex in existing_leaves:
                if ex.duration_type == DurationTypeEnum.FULL_DAY.value:
                    raise ConflictException(
                        detail=f"An active FULL_DAY leave request already exists on {target_date}."
                    )

            # New FULL_DAY blocks any existing request
            if data.duration_type == DurationTypeEnum.FULL_DAY:
                raise ConflictException(
                    detail=f"Cannot submit a FULL_DAY leave when active leaves already exist on {target_date}."
                )

            # New HALF_DAY checks
            if data.duration_type == DurationTypeEnum.HALF_DAY:
                for ex in existing_leaves:
                    if ex.duration_type == DurationTypeEnum.HALF_DAY.value:
                        if ex.half == data.half.value:
                            raise ConflictException(
                                detail=f"An active {data.half.value} leave request already exists on {target_date}."
                            )
                    else:
                        raise ConflictException(
                            detail=f"Cannot combine HALF_DAY with existing {ex.duration_type} leave on {target_date}."
                        )

            # New HOURS checks
            if data.duration_type == DurationTypeEnum.HOURS:
                raise ConflictException(
                    detail=f"Cannot submit an HOURS leave request when other active leave exists on {target_date}."
                )

        # 2. Overlap checks against active WFH requests
        # A FULL_DAY leave cannot overlap an active WFH request
        if data.duration_type == DurationTypeEnum.FULL_DAY:
            existing_wfh = self.wfh_repo.get_active_wfh_on_date(user.id, target_date)
            if existing_wfh:
                raise ConflictException(
                    detail=f"A FULL_DAY leave cannot overlap an active Work-From-Home request on {target_date}."
                )

        # Persist new leave request
        leave = self.leave_repo.create(
            user_id=user.id,
            date=target_date,
            leave_type=data.leave_type.value,
            duration_type=data.duration_type.value,
            days_counted=days_counted,
            half=data.half.value if data.half else None,
            hours=data.hours if data.hours else None,
            reason=data.reason
        )

        return LeaveResponse.model_validate(leave)

    def list_my_leaves(
        self,
        user: User,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[LeaveResponse]:
        """List current user's leave requests, newest first, with optional filters."""
        leaves = self.leave_repo.get_user_leaves(
            user_id=user.id,
            status=status,
            from_date=from_date,
            to_date=to_date
        )
        return [LeaveResponse.model_validate(l) for l in leaves]

    def cancel_leave(self, current_user: User, leave_id: int) -> LeaveResponse:
        """Cancel a pending leave request owned by current user."""
        leave = self.leave_repo.get_by_id(leave_id)
        if not leave:
            raise ResourceNotFoundException(detail="Leave request not found")

        # Hide existence if not owned by caller to prevent enumeration
        if leave.user_id != current_user.id:
            raise ResourceNotFoundException(detail="Leave request not found")

        # Validate transition using centralized State Machine
        RequestStateMachine.validate_transition(
            current_status=RequestStatusEnum(leave.status),
            target_status=RequestStatusEnum.CANCELLED
        )

        leave.status = RequestStatusEnum.CANCELLED.value
        updated_leave = self.leave_repo.update(leave)
        return LeaveResponse.model_validate(updated_leave)
