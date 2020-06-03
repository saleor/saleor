from templated_email import send_templated_mail

from ..celeryconf import app
from ..core.emails import get_email_context
from .models import Invoice


def collect_invoice_data_for_email(invoice_pk, template):
    """Collect the required data for sending emails."""
    invoice = Invoice.objects.get(pk=invoice_pk)
    recipient_email = invoice.order.user.email
    send_kwargs, email_context = get_email_context()

    email_context["number"] = invoice.number
    email_context["download_url"] = invoice.url

    return {
        "recipient_list": [recipient_email],
        "template_name": template,
        "context": email_context,
        **send_kwargs,
    }


@app.task
def send_invoice(invoice_pk):
    """Send an invoice to user of related order with URL to download it."""
    email_data = collect_invoice_data_for_email(invoice_pk, "order/send_invoice")
    send_templated_mail(**email_data)
