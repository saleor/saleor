from collections import defaultdict

from ..graphql.core.dataloaders import DataLoader
from .models import Payment


class PaymentsByOrderIdLoader(DataLoader):
    context_key = "payments_by_order"

    def batch_load(self, keys):
        payments = (
            Payment.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("pk")
        )
        payment_map = defaultdict(list)
        for payment in payments.iterator():
            payment_map[payment.order_id].append(payment)
        return [payment_map.get(order_id, []) for order_id in keys]
