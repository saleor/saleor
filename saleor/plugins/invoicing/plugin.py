from datetime import datetime
from typing import Any, Optional

import pytz

from ...order.models import Invoice, Order
from ..base_plugin import BasePlugin
from . import generate_invoice_number, generate_invoice_pdf


class InvoicingPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.invoicing"
    PLUGIN_NAME = "Invoicing"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Default saleor plugin that handles invoice creation."

    def invoice_request(
        self,
        order: "Order",
        invoice: "Invoice",
        number: Optional[str],
        previous_value: Any,
    ) -> Any:
        invoice.update_invoice(number=generate_invoice_number())
        invoice.created = datetime.now(tz=pytz.utc)
        invoice.save()
        file_name = generate_invoice_pdf(invoice)
        invoice.update_invoice(url=f"http://localhost:8000/invoice/{file_name}")
        invoice.fullfill_invoice()
        return invoice
