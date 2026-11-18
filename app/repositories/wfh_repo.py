from datetime import date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.wfh import WfhRequest
from app.domain.enums import RequestStatusEnum


class WfhRepository:
    """Repository handling database operations for Work-From-Home (WFH) requests."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, wfh_id: int) -> Optional[WfhRequest]:
        """Fetch WFH request by primary key."""
        stmt = select(WfhRequest).where(WfhRequest.id == wfh_id)
        return self.db.scalars(stmt).first()

    def get_active_overlapping_wfh(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[WfhRequest]:
        """Fetch active (PENDING or APPROVED) WFH requests that overlap the given date range."""
        stmt = select(WfhRequest).where(
            WfhRequest.user_id == user_id,
            WfhRequest.start_date <= end_date,
            WfhRequest.end_date >= start_date,
            WfhRequest.status.in_([
                RequestStatusEnum.PENDING.value,
                RequestStatusEnum.APPROVED.value
            ])
        )
        return list(self.db.scalars(stmt).all())

    def get_active_wfh_on_date(self, user_id: int, target_date: date) -> List[WfhRequest]:
        """Fetch active WFH requests covering a specific single date."""
        stmt = select(WfhRequest).where(
            WfhRequest.user_id == user_id,
            WfhRequest.start_date <= target_date,
            WfhRequest.end_date >= target_date,
            WfhRequest.status.in_([
                RequestStatusEnum.PENDING.value,
                RequestStatusEnum.APPROVED.value
            ])
        )
        return list(self.db.scalars(stmt).all())

    def get_user_wfh(
        self,
        user_id: int,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[WfhRequest]:
        """Retrieve WFH requests for a specific user, sorted newest first, with optional filters."""
        stmt = select(WfhRequest).where(WfhRequest.user_id == user_id)

        if status:
            stmt = stmt.where(WfhRequest.status == status.strip().upper())
        if from_date:
            stmt = stmt.where(WfhRequest.end_date >= from_date)
        if to_date:
            stmt = stmt.where(WfhRequest.start_date <= to_date)

        # Sort newest first (created_at desc)
        stmt = stmt.order_by(desc(WfhRequest.created_at))
        return list(self.db.scalars(stmt).all())

    def get_team_wfh(
        self,
        direct_report_ids: List[int],
        status: Optional[str] = "PENDING",
        employee_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[WfhRequest]:
        """Retrieve WFH requests for direct reports with optional filters."""
        if not direct_report_ids:
            return []

        if employee_id:
            if employee_id not in direct_report_ids:
                return []
            stmt = select(WfhRequest).where(WfhRequest.user_id == employee_id)
        else:
            stmt = select(WfhRequest).where(WfhRequest.user_id.in_(direct_report_ids))

        if status:
            stmt = stmt.where(WfhRequest.status == status.strip().upper())
        if from_date:
            stmt = stmt.where(WfhRequest.end_date >= from_date)
        if to_date:
            stmt = stmt.where(WfhRequest.start_date <= to_date)

        stmt = stmt.order_by(desc(WfhRequest.created_at))
        return list(self.db.scalars(stmt).all())

    def create(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        working_days_count: int,
        reason: Optional[str] = None
    ) -> WfhRequest:
        """Create and persist a new WFH request."""
        wfh = WfhRequest(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            working_days_count=working_days_count,
            reason=reason,
            status=RequestStatusEnum.PENDING.value
        )
        self.db.add(wfh)
        self.db.commit()
        self.db.refresh(wfh)
        return wfh

    def update(self, wfh: WfhRequest) -> WfhRequest:
        """Persist changes to an existing WFH request."""
        self.db.commit()
        self.db.refresh(wfh)
        return wfh
