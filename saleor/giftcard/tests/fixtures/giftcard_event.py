import datetime

import pytest
from django.utils import timezone

from ... import GiftCardEvents
from ...models import GiftCardEvent


@pytest.fixture
def gift_card_event(gift_card, order, app, staff_user):
    parameters = {
        "message": "test message",
        "email": "testemail@email.com",
        "tags": ["test tag"],
        "old_tags": ["test old tag"],
        "balance": {
            "currency": "USD",
            "initial_balance": 10,
            "old_initial_balance": 20,
            "current_balance": 10,
            "old_current_balance": 5,
        },
        "expiry_date": datetime.date(2050, 1, 1),
        "old_expiry_date": datetime.date(2010, 1, 1),
    }
    return GiftCardEvent.objects.create(
        user=staff_user,
        app=app,
        gift_card=gift_card,
        order=order,
        type=GiftCardEvents.UPDATED,
        parameters=parameters,
        date=timezone.now() + datetime.timedelta(days=10),
    )
