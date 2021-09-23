import secrets

import pytest
from prices import Money

from .....giftcard import GiftCardEvents
from .....giftcard.models import GiftCard, GiftCardEvent

GIFT_CARD_COUNT_IN_BENCHMARKS = 20


@pytest.fixture
def gift_cards_for_benchmarks(
    staff_user,
    gift_card,
    customer_user,
):

    gift_cards = [
        GiftCard(
            code=secrets.token_hex(8),
            created_by=customer_user,
            created_by_email=customer_user.email,
            initial_balance=Money(10, "USD"),
            current_balance=Money(10, "USD"),
            tag="test-tag",
        )
        for _ in range(GIFT_CARD_COUNT_IN_BENCHMARKS)
    ]
    created_gift_cards = GiftCard.objects.bulk_create(gift_cards)

    parameters = {
        "message": "test message",
        "email": "testemail@email.com",
    }
    events = []
    for gift_card in gift_cards:
        events.append(
            GiftCardEvent(
                user=staff_user,
                gift_card=gift_card,
                type=GiftCardEvents.ISSUED,
                parameters=parameters,
            )
        )

    GiftCardEvent.objects.bulk_create(events)

    return created_gift_cards
