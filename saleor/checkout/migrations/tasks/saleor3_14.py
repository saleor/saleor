from django.db import transaction
from django.db.models.expressions import Exists, OuterRef, Q
from django.forms import model_to_dict

from ....account.models import Address
from ....celeryconf import app
from ....payment.models import TransactionItem
from ...models import Checkout
from ....warehouse.models import Warehouse

# It takes less that a second to process the batch.
# The memory usage peak on celery worker was around 40MB.
BATCH_SIZE = 2000

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250


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
            payment_transactions = list(checkout.payment_transactions.all())
            last_transaction = sorted(
                payment_transactions, key=lambda t: t.modified_at
            )[-1]
            checkout.last_transaction_modified_at = last_transaction.modified_at
            checkouts_to_update.append(checkout)
        with transaction.atomic():
            # lock the batch of objects
            # multiple celery migration tasks called for the same model can cause
            # deadlock. Before updating the objects we need to lock them.
            _checkouts_lock = list(checkouts.select_for_update(of=(["self"])))
            Checkout.objects.bulk_update(
                checkouts_to_update, ["last_transaction_modified_at"]
            )
        update_transaction_modified_at_in_checkouts.delay()


@app.task
def update_checkout_refundable():
    with_transactions = TransactionItem.objects.filter(
        Q(checkout_id=OuterRef("pk"))
        & (Q(authorized_value__gt=0) | Q(charged_value__gt=0))
    )
    checkout_to_update = Checkout.objects.filter(
        Exists(with_transactions), automatically_refundable=False
    ).values_list("pk", flat=True)[:BATCH_SIZE]

    if checkout_to_update:
        with transaction.atomic():
            # lock the batch of objects
            # multiple celery migration tasks called for the same model can cause
            # deadlock. Before updating the objects we need to lock them.
            _checkout_lock = list(checkout_to_update.select_for_update(of=(["self"])))
            Checkout.objects.filter(pk__in=checkout_to_update).update(
                automatically_refundable=True
            )

        update_checkout_refundable.delay()


@app.task
def update_checkout_addresses_task():
    qs = Checkout.objects.filter(
        Exists(Warehouse.objects.filter(address_id=OuterRef("shipping_address_id"))),
    )
    checkout_ids = qs.values_list("pk", flat=True)[:ADDRESS_UPDATE_BATCH_SIZE]
    addresses = []
    if checkout_ids:
        checkouts = Checkout.objects.filter(pk__in=checkout_ids)
        for checkout in checkouts:
            if cc_address := checkout.shipping_address:
                checkout_address = Address(**model_to_dict(cc_address, exclude=["id"]))
                checkout.shipping_address = checkout_address
                addresses.append(checkout_address)
        Address.objects.bulk_create(addresses, ignore_conflicts=True)
        Checkout.objects.bulk_update(checkouts, ["shipping_address"])
        update_checkout_addresses_task.delay()
