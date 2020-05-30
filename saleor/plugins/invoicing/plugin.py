from typing import Any, Optional
from uuid import uuid4

from django.core.files.base import ContentFile

from ...core import JobStatus
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
        file_content, creation_date = generate_invoice_pdf(invoice_job.invoice)
        invoice_job.invoice.created = creation_date
        invoice_job.invoice.update_invoice(number=generate_invoice_number())
        invoice_job.invoice.save()
        invoice_job.invoice.invoice_file.save(
            f"{uuid4()}.pdf", ContentFile(file_content)
        )
        invoice_job.status = JobStatus.SUCCESS
        invoice_job.save()
        return invoice_job
