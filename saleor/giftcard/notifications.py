from typing import TYPE_CHECKING

from ..account.notifications import get_default_user_payload
from ..core.notification.utils import get_site_context
from ..core.notify_events import NotifyEventType
from ..core.prices import quantize_price
from ..graphql.core.utils import to_global_id_or_none

if TYPE_CHECKING:
    from .models import GiftCard


def send_gift_card_notification(
    requester_user,
    app,
    customer_user,
    email,
    gift_card,
    manager,
    channel_slug,
    *,
    resending,
):
    """Trigger sending a gift card notification for the given recipient."""
    payload = {
        "gift_card": get_default_gift_card_payload(gift_card),
        "user": get_default_user_payload(customer_user) if customer_user else None,
        "requester_user_id": to_global_id_or_none(requester_user)
        if requester_user
        else None,
        "requester_app_id": to_global_id_or_none(app) if app else None,
        "recipient_email": email,
        "resending": resending,
        **get_site_context(),
    }
    manager.notify(
        NotifyEventType.SEND_GIFT_CARD, payload=payload, channel_slug=channel_slug
    )
    manager.gift_card_sent(gift_card, channel_slug, email)


def get_default_gift_card_payload(gift_card: "GiftCard"):
    return {
        "id": to_global_id_or_none(gift_card),
        "code": gift_card.code,
        "balance": quantize_price(gift_card.current_balance_amount, gift_card.currency),
        "currency": gift_card.currency,
    }
