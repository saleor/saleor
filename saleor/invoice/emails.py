from templated_email import send_templated_mail

from ..account.models import User
from ..celeryconf import app
from ..core.emails import get_email_context
from ..invoice import events
from ..plugins.manager import get_plugins_manager
from .models import Invoice


def collect_invoice_data_for_email(invoice, template):
    """Collect the required data for sending emails."""
    send_kwargs, email_context = get_email_context()

    email_context["number"] = invoice.number
    email_context["download_url"] = invoice.url

    return {
        "recipient_list": [invoice.order.get_customer_email()],
        "template_name": template,
        "context": email_context,
        **send_kwargs,
    }


@app.task
def send_invoice(invoice_pk, staff_user_pk):
    """Send an invoice to user of related order with URL to download it."""
    invoice = Invoice.objects.select_related("order").get(pk=invoice_pk)
    email_data = collect_invoice_data_for_email(invoice, "order/send_invoice")
    send_templated_mail(**email_data)
    events.invoice_sent_event(user=User.objects.get(pk=staff_user_pk), invoice=invoice)
    manager = get_plugins_manager()
    manager.invoice_sent(invoice, invoice.order.get_customer_email())
