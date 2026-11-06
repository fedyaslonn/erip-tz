from exceptions.validation_exceptions import DealAlreadyProcessedError
from persistence.models import TransactionStatus


class TransactionStateMachine:
    ALLOWED_TRANSITIONS = {
        TransactionStatus.PENDING: {
            TransactionStatus.COMPLETED,
            TransactionStatus.REJECTED,
        },
        TransactionStatus.COMPLETED: set(),
        TransactionStatus.REJECTED: set(),
    }

    @classmethod
    def validate_transition(
        cls,
        deal_id: str,
        current_status: TransactionStatus,
        new_status: TransactionStatus,
    ) -> None:
        allowed_next_states = cls.ALLOWED_TRANSITIONS.get(current_status, set())

        if new_status not in allowed_next_states:
            raise DealAlreadyProcessedError(
                deal_id=deal_id, status=current_status.value
            )
