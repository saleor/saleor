from collections import defaultdict

from ...payment.models import Transaction, TransactionEvent, TransactionItem
from ..core.dataloaders import DataLoader


class TransactionEventByTransactionIdLoader(DataLoader):
    context_key = "transaction_event_by_transaction_id"

    def batch_load(self, keys):
        events = (
            TransactionEvent.objects.using(self.database_connection_name)
            .filter(transaction_id__in=keys)
            .order_by("-created_at")
        )
        event_map = defaultdict(list)
        for event in events:
            event_map[event.transaction_id].append(event)
        return [event_map.get(transaction_id, []) for transaction_id in keys]


class TransactionItemByIDLoader(DataLoader):
    context_key = "transaction_items_by_id"

    def batch_load(self, keys):
        transactions = TransactionItem.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [transactions.get(transaction_id) for transaction_id in keys]


class TransactionByPaymentIdLoader(DataLoader):
    context_key = "transaction_by_payment_id"

    def batch_load(self, keys):
        transactions = Transaction.objects.using(self.database_connection_name).filter(
            payment_id__in=keys
        )
        transaction_group = defaultdict(list)

        for transaction in transactions:
            transaction_group[transaction.payment_id].append(transaction)

        return [transaction_group.get(payment_id, []) for payment_id in keys]
