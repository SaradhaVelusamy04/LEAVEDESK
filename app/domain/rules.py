from datetime import date, timedelta
from typing import Optional
from app.domain.enums import DurationTypeEnum, HalfEnum
from app.core.exceptions import ValidationException


def validate_and_calculate_leave_days(
    duration_type: DurationTypeEnum,
    half: Optional[HalfEnum] = None,
    hours: Optional[int] = None
) -> float:
    """Validate duration combinations and calculate days_counted.
    
    Rules:
    - FULL_DAY: no extra fields, counted as 1.0 day.
    - HALF_DAY: requires half (FIRST_HALF or SECOND_HALF), counted as 0.5 day.
    - HOURS: requires whole number hours (1, 2, or 3), counted as hours / 8.
    """
    if duration_type == DurationTypeEnum.FULL_DAY:
        if half is not None:
            raise ValidationException(detail="Field 'half' must not be provided for FULL_DAY duration")
        if hours is not None:
            raise ValidationException(detail="Field 'hours' must not be provided for FULL_DAY duration")
        return 1.0

    elif duration_type == DurationTypeEnum.HALF_DAY:
        if half is None:
            raise ValidationException(detail="Field 'half' is required for HALF_DAY duration")
        if half not in (HalfEnum.FIRST_HALF, HalfEnum.SECOND_HALF):
            raise ValidationException(detail="Field 'half' must be either FIRST_HALF or SECOND_HALF")
        if hours is not None:
            raise ValidationException(detail="Field 'hours' must not be provided for HALF_DAY duration")
        return 0.5

    elif duration_type == DurationTypeEnum.HOURS:
        if half is not None:
            raise ValidationException(detail="Field 'half' must not be provided for HOURS duration")
        if hours is None:
            raise ValidationException(detail="Field 'hours' is required for HOURS duration")
        if not isinstance(hours, int) or isinstance(hours, bool):
            raise ValidationException(detail="Field 'hours' must be an integer")
        if hours not in (1, 2, 3):
            raise ValidationException(detail="Field 'hours' must be an integer whole number in 1, 2, or 3")
        return hours / 8.0

    else:
        raise ValidationException(detail=f"Unsupported duration type: {duration_type}")


def calculate_working_days(start_date: date, end_date: date) -> int:
    """Calculate the number of working days (Monday-Friday) between start_date and end_date inclusive.
    
    Enforces:
    - start_date <= end_date
    - At least 1 working day
    - At most 2 working days
    """
    if start_date > end_date:
        raise ValidationException(detail="start_date must be on or before end_date")

    working_days = 0
    current_date = start_date
    one_day = timedelta(days=1)

    while current_date <= end_date:
        # Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
        if current_date.weekday() < 5:
            working_days += 1
        current_date += one_day

    if working_days == 0:
        raise ValidationException(
            detail="The requested date range does not contain any working days (Monday-Friday)"
        )

    if working_days > 2:
        raise ValidationException(
            detail=f"Work-From-Home requests cannot exceed 2 working days. Selected range contains {working_days} working days."
        )

    return working_days
