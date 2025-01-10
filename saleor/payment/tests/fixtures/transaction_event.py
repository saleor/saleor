from decimal import Decimal
from typing import Callable

import pytest

from ....payment.models import TransactionEvent, TransactionItem


@pytest.fixture
def transaction_events_generator() -> (
    Callable[
        [list[str], list[str], list[Decimal], TransactionItem], list[TransactionEvent]
    ]
):
    def factory(
        psp_references: list[str],
        types: list[str],
        amounts: list[Decimal],
        transaction: TransactionItem,
    ):
        return TransactionEvent.objects.bulk_create(
            TransactionEvent(
                transaction=transaction,
                psp_reference=reference,
                type=event_type,
                amount_value=amount,
                include_in_calculations=True,
                currency=transaction.currency,
            )
            for reference, event_type, amount in zip(psp_references, types, amounts)
        )

    return factory
