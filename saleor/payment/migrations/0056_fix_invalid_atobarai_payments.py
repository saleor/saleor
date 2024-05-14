from django.db import migrations
from django.db.models import Exists, OuterRef

# Batch size of size 3000 took about 0.2s and consume about 5MB memory usage
PAYMENT_BATCH_SIZE = 3000


def fix_invalid_atobarai_payments(apps, schema_editor):
    Payment = apps.get_model("payment", "Payment")
    not_charged_active_payments = Payment.objects.filter(
        is_active=True,
        charge_status="not-charged",
        captured_amount=0,
        gateway="saleor.payments.np-atobarai",
    )
    payments = Payment.objects.filter(
        Exists(not_charged_active_payments.filter(order_id=OuterRef("order_id"))),
        is_active=False,
        charge_status__in=[
            "fully-charged",
            "partially-charged",
        ],
        captured_amount__gt=0,
        gateway="saleor.payments.np-atobarai",
    )
    for ids in queryset_in_batches(payments):
        payments_to_activate = Payment.objects.filter(pk__in=ids)

        related_order_ids = payments_to_activate.values("order_id")
        payments_to_deactivate = Payment.objects.filter(
            order_id__in=related_order_ids, is_active=True
        ).exclude(pk__in=ids)

        payments_to_deactivate.update(is_active=False)
        payments_to_activate.update(is_active=True)


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:PAYMENT_BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0055_add_constraints_from_indexes"),
    ]

    operations = [
        migrations.RunPython(fix_invalid_atobarai_payments, migrations.RunPython.noop),
    ]
