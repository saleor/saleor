from django.db.models.expressions import Exists, OuterRef

from ....celeryconf import app
from ....payment.models import TransactionItem
from ...models import Checkout

# It takes less that a second to process the batch.
# The memory usage peak on celery worker was around 40MB.
BATCH_SIZE = 2000


@app.task
def update_transaction_modified_at_in_checkouts():
    checkouts_without_modified_at = Checkout.objects.filter(
        Exists(TransactionItem.objects.filter(checkout_id=OuterRef("pk"))),
        last_transaction_modified_at__isnull=True,
    ).values_list("pk", flat=True)[:BATCH_SIZE]

    if checkouts_without_modified_at:
        checkouts = Checkout.objects.filter(
            pk__in=checkouts_without_modified_at
        ).prefetch_related("payment_transactions")
        checkouts_to_update = []
        for checkout in checkouts:
            transactions = list(checkout.payment_transactions.all())
            last_transaction = sorted(transactions, key=lambda t: t.modified_at)[-1]
            checkout.last_transaction_modified_at = last_transaction.modified_at
            checkouts_to_update.append(checkout)
        Checkout.objects.bulk_update(
            checkouts_to_update, ["last_transaction_modified_at"]
        )
        update_transaction_modified_at_in_checkouts.delay()
