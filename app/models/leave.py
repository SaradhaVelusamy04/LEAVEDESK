from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.domain.enums import RequestStatusEnum


class LeaveRequest(Base):
    """Leave request record submitted by an employee or manager."""
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    leave_type = Column(String(20), nullable=False)
    duration_type = Column(String(20), nullable=False)
    half = Column(String(20), nullable=True)
    hours = Column(Integer, nullable=True)
    days_counted = Column(Float, nullable=False)
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
    user = relationship("User", foreign_keys=[user_id], backref="leave_requests")
    decider = relationship("User", foreign_keys=[decided_by])

    def __repr__(self) -> str:
        return f"<LeaveRequest id={self.id} user_id={self.user_id} date={self.date} status='{self.status}'>"
