from ..core.notifications import get_site_context
from ..core.notify_events import NotifyEventType


def send_gift_card_notification(email, gift_card, manager):
    """Trigger sending a gift card notification for the given recipient."""
    payload = {
        "recipient_email": email,
        "code": gift_card.code,
        **get_site_context(),
    }
    manager.notify(NotifyEventType.SEND_GIFT_CARD, payload=payload)
