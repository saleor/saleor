from ....celeryconf import app
from ...models import TransactionItem

# Batch size of size 5000 is about 5MB memory usage in task
BATCH_SIZE = 5000


@app.task
def convert_transaction_void_to_cancel_task():
    qs = TransactionItem.objects.filter(available_actions__contains=["void"])
    transaction_ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if transaction_ids:
        transactions = TransactionItem.objects.filter(pk__in=transaction_ids)
        for transaction_item in transactions:
            current_available_actions = transaction_item.available_actions
            if "void" in current_available_actions:
                current_available_actions.remove("void")
                if "cancel" not in current_available_actions:
                    current_available_actions.append("cancel")
        TransactionItem.objects.bulk_update(transactions, ["available_actions"])
        convert_transaction_void_to_cancel_task.delay()
