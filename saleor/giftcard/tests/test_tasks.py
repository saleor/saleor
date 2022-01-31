import datetime

import pytest
from django.utils import timezone

from .. import GiftCardEvents
from ..models import GiftCard
from ..tasks import deactivate_expired_cards_task


def test_deactivate_expired_cards_task(
    gift_card, gift_card_used, gift_card_expiry_date, gift_card_created_by_staff
):
    # given
    gift_card.expiry_date = datetime.date.today() - datetime.timedelta(days=1)
    gift_card_used.expiry_date = datetime.date.today() - datetime.timedelta(days=10)
    gift_card_created_by_staff.expiry_date = datetime.date.today() - datetime.timedelta(
        days=10
    )
    gift_card_created_by_staff.is_active = False
    gift_cards = [gift_card, gift_card_used]
    GiftCard.objects.bulk_update(
        gift_cards + [gift_card_created_by_staff], ["expiry_date", "is_active"]
    )

    for card in gift_cards:
        assert card.is_active

    # when
    deactivate_expired_cards_task()

    # then
    for card in gift_cards:
        card.refresh_from_db()
        assert not card.is_active
        assert card.events.filter(type=GiftCardEvents.DEACTIVATED)

    assert not gift_card_created_by_staff.events.filter(type=GiftCardEvents.DEACTIVATED)

    gift_card_expiry_date.refresh_from_db()
    assert gift_card_expiry_date.is_active


@pytest.mark.parametrize(
    "expiry_date",
    [
        timezone.now().date(),
        timezone.now().date() + datetime.timedelta(days=1),
    ],
)
def test_deactivate_expired_cards_task_cards_not_deactivated(
    expiry_date, gift_card, gift_card_used, gift_card_expiry_date
):
    # given
    gift_card.expiry_date = expiry_date
    gift_card_used.expiry_date = expiry_date
    gift_cards = [gift_card, gift_card_used]
    GiftCard.objects.bulk_update(gift_cards, ["expiry_date"])

    for card in gift_cards:
        assert card.is_active

    # when
    deactivate_expired_cards_task()

    # then
    for card in gift_cards:
        card.refresh_from_db()
        assert card.is_active

    gift_card_expiry_date.refresh_from_db()
    assert gift_card_expiry_date.is_active
