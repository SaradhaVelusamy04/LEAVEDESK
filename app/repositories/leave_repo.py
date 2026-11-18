from datetime import date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.leave import LeaveRequest
from app.domain.enums import RequestStatusEnum


class LeaveRepository:
    """Repository handling database operations for Leave requests."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, leave_id: int) -> Optional[LeaveRequest]:
        """Fetch leave request by primary key."""
        stmt = select(LeaveRequest).where(LeaveRequest.id == leave_id)
        return self.db.scalars(stmt).first()

    def get_active_leaves_on_date(self, user_id: int, target_date: date) -> List[LeaveRequest]:
        """Fetch active (PENDING or APPROVED) leave requests for a user on a given date."""
        stmt = select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.date == target_date,
            LeaveRequest.status.in_([
                RequestStatusEnum.PENDING.value,
                RequestStatusEnum.APPROVED.value
            ])
        )
        return list(self.db.scalars(stmt).all())

    def get_active_leaves_in_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[LeaveRequest]:
        """Fetch active leave requests for a user within a date range."""
        stmt = select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.date >= start_date,
            LeaveRequest.date <= end_date,
            LeaveRequest.status.in_([
                RequestStatusEnum.PENDING.value,
                RequestStatusEnum.APPROVED.value
            ])
        )
        return list(self.db.scalars(stmt).all())

    def get_user_leaves(
        self,
        user_id: int,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[LeaveRequest]:
        """Retrieve leave requests for a specific user, sorted newest first, with optional filters."""
        stmt = select(LeaveRequest).where(LeaveRequest.user_id == user_id)

        if status:
            stmt = stmt.where(LeaveRequest.status == status.strip().upper())
        if from_date:
            stmt = stmt.where(LeaveRequest.date >= from_date)
        if to_date:
            stmt = stmt.where(LeaveRequest.date <= to_date)

        # Sort newest first (created_at desc)
        stmt = stmt.order_by(desc(LeaveRequest.created_at))
        return list(self.db.scalars(stmt).all())

    def get_team_leaves(
        self,
        direct_report_ids: List[int],
        status: Optional[str] = "PENDING",
        employee_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[LeaveRequest]:
        """Retrieve leave requests for direct reports with optional filters."""
        if not direct_report_ids:
            return []

        # If employee_id is passed, filter specifically for that employee (if in direct reports)
        if employee_id:
            if employee_id not in direct_report_ids:
                return []
            stmt = select(LeaveRequest).where(LeaveRequest.user_id == employee_id)
        else:
            stmt = select(LeaveRequest).where(LeaveRequest.user_id.in_(direct_report_ids))

        if status:
            stmt = stmt.where(LeaveRequest.status == status.strip().upper())
        if from_date:
            stmt = stmt.where(LeaveRequest.date >= from_date)
        if to_date:
            stmt = stmt.where(LeaveRequest.date <= to_date)

        stmt = stmt.order_by(desc(LeaveRequest.created_at))
        return list(self.db.scalars(stmt).all())

    def create(
        self,
        user_id: int,
        date: date,
        leave_type: str,
        duration_type: str,
        days_counted: float,
        half: Optional[str] = None,
        hours: Optional[int] = None,
        reason: Optional[str] = None
    ) -> LeaveRequest:
        """Create and persist a new leave request."""
        leave = LeaveRequest(
            user_id=user_id,
            date=date,
            leave_type=leave_type,
            duration_type=duration_type,
            days_counted=days_counted,
            half=half,
            hours=hours,
            reason=reason,
            status=RequestStatusEnum.PENDING.value
        )
        self.db.add(leave)
        self.db.commit()
        self.db.refresh(leave)
        return leave

    def update(self, leave: LeaveRequest) -> LeaveRequest:
        """Persist changes to an existing leave request."""
        self.db.commit()
        self.db.refresh(leave)
        return leave
