from ..lock_objects import gift_card_qs_select_for_update
from ..models import GiftCard


def test_gift_card_qs_select_for_update_returns_giftcard_queryset(gift_card):
    # when
    qs = gift_card_qs_select_for_update()

    # then
    assert qs.model is GiftCard
    assert qs.query.select_for_update is True
