from typing import Dict, Set
from app.domain.enums import RequestStatusEnum
from app.core.exceptions import ConflictException


class RequestStateMachine:
    """Centralized state machine governing request lifecycle status transitions."""

    # Explicit allowed transitions map
    _ALLOWED_TRANSITIONS: Dict[RequestStatusEnum, Set[RequestStatusEnum]] = {
        RequestStatusEnum.PENDING: {
            RequestStatusEnum.APPROVED,
            RequestStatusEnum.REJECTED,
            RequestStatusEnum.CANCELLED
        },
        RequestStatusEnum.APPROVED: set(),  # Terminal state
        RequestStatusEnum.REJECTED: set(),  # Terminal state
        RequestStatusEnum.CANCELLED: set()  # Terminal state
    }

    @classmethod
    def can_transition(
        cls,
        current_status: RequestStatusEnum,
        target_status: RequestStatusEnum
    ) -> bool:
        """Check if transition from current_status to target_status is valid."""
        allowed_targets = cls._ALLOWED_TRANSITIONS.get(current_status, set())
        return target_status in allowed_targets

    @classmethod
    def validate_transition(
        cls,
        current_status: RequestStatusEnum,
        target_status: RequestStatusEnum
    ) -> None:
        """Validate status transition and raise HTTP 409 Conflict if disallowed."""
        if not cls.can_transition(current_status, target_status):
            raise ConflictException(
                detail=(
                    f"Invalid status transition from '{current_status.value}' to '{target_status.value}'. "
                    f"Requests in '{current_status.value}' status cannot be transitioned."
                )
            )
