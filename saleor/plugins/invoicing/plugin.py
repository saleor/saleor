from typing import Any, Optional

from django.urls import reverse

from ...core.utils import build_absolute_uri
from ...graphql.invoice.enums import InvoiceStatus
from ...invoice.models import InvoiceJob
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
        invoice_job: "InvoiceJob",
        number: Optional[str],
        previous_value: Any,
    ) -> Any:
        file_hash, creation_date = generate_invoice_pdf(invoice_job.invoice)
        invoice_job.invoice.created = creation_date
        invoice_job.invoice.update_invoice(number=generate_invoice_number())
        invoice_job.invoice.save()
        invoice_job.invoice.update_invoice(
            url=build_absolute_uri(reverse("download-invoice", args=[file_hash]))
        )
        invoice_job.status = InvoiceStatus.READY
        invoice_job.save()
        return invoice_job
