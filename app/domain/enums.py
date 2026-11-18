from enum import Enum


class RoleEnum(str, Enum):
    """User roles within LeaveDesk."""
    EMPLOYEE = "employee"
    MANAGER = "manager"


class LeaveTypeEnum(str, Enum):
    """Supported types of leave."""
    CASUAL = "CASUAL"
    SICK = "SICK"
    EARNED = "EARNED"


class DurationTypeEnum(str, Enum):
    """Supported leave durations."""
    FULL_DAY = "FULL_DAY"
    HALF_DAY = "HALF_DAY"
    HOURS = "HOURS"


class HalfEnum(str, Enum):
    """Allowed half-day slots."""
    FIRST_HALF = "FIRST_HALF"
    SECOND_HALF = "SECOND_HALF"


class RequestStatusEnum(str, Enum):
    """Lifecycle status for Leave and WFH requests."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class RequestTypeEnum(str, Enum):
    """Type of request for reporting."""
    LEAVE = "LEAVE"
    WFH = "WFH"
