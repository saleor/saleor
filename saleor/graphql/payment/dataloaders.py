from collections import defaultdict

from ...payment.models import TransactionEvent
from ..core.dataloaders import DataLoader


class TransactionEventByTransactionIdLoader(DataLoader):
    context_key = "transaction_event_by_transaction_id"

    def batch_load(self, keys):
        events = (
            TransactionEvent.objects.using(self.database_connection_name)
            .filter(transaction_id__in=keys)
            .order_by("pk")
        )
        event_map = defaultdict(list)
        for event in events:
            event_map[event.transaction_id].append(event)
        return [event_map.get(transaction_id, []) for transaction_id in keys]
