from django.db import migrations
from django.db.models import Exists, OuterRef, Q, Subquery

# It takes less that a second to process the batch.
# The memory usage peak on celery worker was around 40MB.
BATCH_SIZE = 2000


def add_transaction_modified_at_to_checkouts(apps, _schema_editor):
    Checkout = apps.get_model("checkout", "Checkout")
    TransactionItem = apps.get_model("payment", "TransactionItem")

    while True:
        checkouts_without_modified_at = Checkout.objects.filter(
            Exists(TransactionItem.objects.filter(checkout_id=OuterRef("pk"))),
            last_transaction_modified_at__isnull=True,
        ).values_list("pk", flat=True)[:BATCH_SIZE]
        if not checkouts_without_modified_at:
            break
        transaction_subquery = TransactionItem.objects.filter(
            checkout_id=OuterRef("pk")
        ).order_by("-modified_at")
        Checkout.objects.filter(pk__in=checkouts_without_modified_at).update(
            last_transaction_modified_at=Subquery(
                transaction_subquery.values("modified_at")[:1]
            )
        )


def calculate_checkout_refundable(apps, _schema_editor):
    Checkout = apps.get_model("checkout", "Checkout")
    TransactionItem = apps.get_model("payment", "TransactionItem")

    with_transactions = TransactionItem.objects.filter(
        Q(checkout_id=OuterRef("pk"))
        & (Q(authorized_value__gt=0) | Q(charged_value__gt=0))
    )

    while True:
        checkout_to_update = Checkout.objects.filter(
            Exists(with_transactions), automatically_refundable=False
        ).values_list("pk", flat=True)[:BATCH_SIZE]
        if not checkout_to_update:
            break

        Checkout.objects.filter(pk__in=checkout_to_update).update(
            automatically_refundable=True
        )


class Migration(migrations.Migration):
    dependencies = [
        ("checkout", "0061_checkout_last_transaction_modified_at_and_refundable"),
    ]

    operations = [
        migrations.RunPython(
            add_transaction_modified_at_to_checkouts,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            calculate_checkout_refundable,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
