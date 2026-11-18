from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.domain.enums import RequestStatusEnum


class WfhRequest(Base):
    """Work-From-Home (WFH) request submitted by an employee or manager."""
    __tablename__ = "wfh_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    working_days_count = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=RequestStatusEnum.PENDING.value, index=True)

    # Decision audit trail
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decision_comment = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="wfh_requests")
    decider = relationship("User", foreign_keys=[decided_by])

    def __repr__(self) -> str:
        return f"<WfhRequest id={self.id} user_id={self.user_id} span={self.start_date}..{self.end_date} status='{self.status}'>"
