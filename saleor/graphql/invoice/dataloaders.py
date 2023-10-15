from collections import defaultdict

from ...invoice.models import Invoice
from ..core.dataloaders import DataLoader


class InvoicesByOrderIdLoader(DataLoader):
    context_key = "invoices_by_order_id"

    def batch_load(self, keys):
        invoices = (
            Invoice.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("pk")
        )
        invoices_by_order_map = defaultdict(list)
        for invoice in invoices:
            invoices_by_order_map[invoice.order_id].append(invoice)
        return [invoices_by_order_map.get(order_id, []) for order_id in keys]
