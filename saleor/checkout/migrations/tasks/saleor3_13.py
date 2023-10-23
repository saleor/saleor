from decimal import Decimal

from django.db.models.expressions import Exists, OuterRef

from ....celeryconf import app
from ....payment.models import TransactionItem
from ...models import Checkout, CheckoutLine

BATCH_SIZE = 500


@app.task
def fix_statuses_for_empty_checkouts_task():
    empty_checkouts_fully_charged_ids = Checkout.objects.filter(
        ~Exists(CheckoutLine.objects.filter(checkout_id=OuterRef("pk"))),
        charge_status="full",
        total_gross_amount__lte=Decimal(0),
    ).values_list("pk", flat=True)[:BATCH_SIZE]

    trigger_task = False
    if empty_checkouts_fully_charged_ids:
        trigger_task = True
        Checkout.objects.filter(pk__in=empty_checkouts_fully_charged_ids).update(
            charge_status="none",
        )

    empty_checkouts_fully_authorized = Checkout.objects.filter(
        ~Exists(CheckoutLine.objects.filter(checkout_id=OuterRef("pk"))),
        authorize_status="full",
        total_gross_amount__lte=Decimal(0),
    )

    empty_checkouts_fully_authorized_without_transaction_ids = (
        empty_checkouts_fully_authorized.filter(
            ~Exists(TransactionItem.objects.filter(checkout_id=OuterRef("pk"))),
        ).values_list("pk", flat=True)[:BATCH_SIZE]
    )

    if empty_checkouts_fully_authorized_without_transaction_ids:
        trigger_task = True
        Checkout.objects.filter(
            pk__in=empty_checkouts_fully_authorized_without_transaction_ids
        ).update(
            authorize_status="none",
        )

    checkout_fully_authorized_with_transaction_ids = (
        empty_checkouts_fully_authorized.filter(
            Exists(
                TransactionItem.objects.filter(
                    checkout_id=OuterRef("pk"),
                    authorized_value__lte=Decimal(0),
                    charged_value__lte=Decimal(0),
                )
            ),
        ).values_list("pk", flat=True)[:BATCH_SIZE]
    )

    if checkout_fully_authorized_with_transaction_ids:
        trigger_task = True
        Checkout.objects.filter(
            pk__in=checkout_fully_authorized_with_transaction_ids
        ).update(
            authorize_status="none",
        )

    if trigger_task:
        fix_statuses_for_empty_checkouts_task.delay()
