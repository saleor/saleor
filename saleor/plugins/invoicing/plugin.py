from typing import Any, Optional
from uuid import uuid4

from django.core.files.base import ContentFile

from ...core import JobStatus
from ...invoice.models import Invoice
from ...order.models import Order
from ..base_plugin import BasePlugin
from .utils import generate_invoice_number, generate_invoice_pdf


class InvoicingPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.invoicing"
    PLUGIN_NAME = "Invoicing"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Built-in saleor plugin that handles invoice creation."

    def invoice_request(
        self,
        order: "Order",
        invoice: "Invoice",
        number: Optional[str],
        previous_value: Any,
    ) -> Any:
        invoice.update_invoice(number=generate_invoice_number())
        file_content, creation_date = generate_invoice_pdf(invoice)
        invoice.created = creation_date
        invoice.invoice_file.save(
            f"invoice-{invoice.number}-order-{order.id}-{uuid4()}.pdf",
            ContentFile(file_content),
        )
        invoice.status = JobStatus.SUCCESS
        invoice.save(
            update_fields=["created", "number", "invoice_file", "status", "updated_at"]
        )
        return invoice
