from typing import Any, Optional

from django.urls import reverse

from ...core.utils import build_absolute_uri
from ...order.models import Invoice, Order
from ..base_plugin import BasePlugin
from . import generate_invoice_number, generate_invoice_pdf


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
        file_hash, creation_date = generate_invoice_pdf(invoice)
        invoice.created = creation_date
        invoice.update_invoice(number=generate_invoice_number())
        invoice.save()
        invoice.update_invoice(
            url=build_absolute_uri(reverse("download-invoice", args=[file_hash]))
        )
        invoice.fullfill_invoice()
        return invoice
