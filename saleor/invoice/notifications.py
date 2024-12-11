from typing import TYPE_CHECKING, Optional

from ..core.notification.utils import get_site_context
from ..core.notify import NotifyEventType, NotifyHandler
from ..graphql.core.utils import to_global_id_or_none

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App
    from ..plugins.manager import PluginsManager
    from .models import Invoice


def get_invoice_payload(invoice):
    return {
        "id": to_global_id_or_none(invoice),
        "number": invoice.number,
        "download_url": invoice.url,
        "order_id": to_global_id_or_none(invoice.order),
    }


def send_invoice(
    invoice: "Invoice",
    staff_user: "User",
    app: Optional["App"],
    manager: "PluginsManager",
):
    """Send an invoice to user of related order with URL to download it."""

    def _generate_payload():
        payload = {
            "invoice": get_invoice_payload(invoice),
            "recipient_email": invoice.order.get_customer_email(),  # type: ignore[union-attr]
            "requester_user_id": to_global_id_or_none(staff_user),
            "requester_app_id": to_global_id_or_none(app) if app else None,
            **get_site_context(),
        }
        return payload

    channel_slug = None
    if invoice.order and invoice.order.channel:
        channel_slug = invoice.order.channel.slug
    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.INVOICE_READY,
        payload_func=handler.payload,
        channel_slug=channel_slug,
    )
    if invoice.order:
        manager.invoice_sent(invoice, invoice.order.get_customer_email())
