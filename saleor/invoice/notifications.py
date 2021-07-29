from typing import TYPE_CHECKING, Optional

from ..core.notifications import get_site_context
from ..core.notify_events import NotifyEventType

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App
    from ..plugins.manager import PluginsManager
    from .models import Invoice


def get_invoice_payload(invoice):
    return {
        "id": invoice.id,
        "number": invoice.number,
        "download_url": invoice.url,
        "order_id": invoice.order_id,
    }


def send_invoice(
    invoice: "Invoice",
    staff_user: "User",
    app: Optional["App"],
    manager: "PluginsManager",
):
    """Send an invoice to user of related order with URL to download it."""
    payload = {
        "invoice": get_invoice_payload(invoice),
        "recipient_email": invoice.order.get_customer_email(),  # type: ignore
        "requester_user_id": staff_user.id,
        "requester_app_id": app.id if app else None,
        **get_site_context(),
    }
    manager.notify(NotifyEventType.INVOICE_READY, payload)  # type: ignore
    manager.invoice_sent(invoice, invoice.order.get_customer_email())  # type: ignore
