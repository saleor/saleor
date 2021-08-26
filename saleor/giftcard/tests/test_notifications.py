from unittest import mock

from ...account.notifications import get_default_user_payload
from ...core.notify_events import NotifyEventType
from ...plugins.manager import get_plugins_manager
from ..notifications import get_default_gift_card_payload, send_gift_card_notification


def test_get_default_gift_card_payload(gift_card):
    payload = get_default_gift_card_payload(gift_card)
    assert payload == {
        "id": gift_card.id,
        "code": gift_card.code,
        "balance": gift_card.current_balance_amount,
        "currency": gift_card.currency,
    }


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_gift_card_notification(
    mocked_notify, staff_user, customer_user, gift_card, channel_USD
):
    manager = get_plugins_manager()
    resending = False
    send_gift_card_notification(
        staff_user,
        None,
        customer_user,
        customer_user.email,
        gift_card,
        manager,
        channel_USD.slug,
        resending=resending,
    )

    expected_payload = {
        "gift_card": get_default_gift_card_payload(gift_card),
        "user": get_default_user_payload(customer_user) if customer_user else None,
        "requester_user_id": staff_user.id,
        "requester_app_id": None,
        "recipient_email": customer_user.email,
        "resending": resending,
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.SEND_GIFT_CARD,
        payload=expected_payload,
        channel_slug=channel_USD.slug,
    )
