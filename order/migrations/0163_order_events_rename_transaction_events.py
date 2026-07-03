from django.db import migrations, transaction
from django.db.models import QuerySet

from ..models import OrderEvent

BATCH_SIZE = 5000


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


def update_type_to_transaction_cancel_requested(qs: QuerySet[OrderEvent]):
    with transaction.atomic():
        # lock the batch of objects
        _events = list(qs.select_for_update(of=(["self"])))
        qs.update(type="transaction_cancel_requested")


def order_events_rename_transaction_void_events_task(order_event_model):
    events = order_event_model.objects.filter(
        type="transaction_void_requested"
    ).order_by("pk")

    for ids in queryset_in_batches(events):
        qs = order_event_model.objects.filter(pk__in=ids)
        update_type_to_transaction_cancel_requested(qs)


def update_type_to_transaction_charge_requested(qs: QuerySet[OrderEvent]):
    with transaction.atomic():
        # lock the batch of objects
        _events = list(qs.select_for_update(of=(["self"])))
        qs.update(type="transaction_charge_requested")


def order_events_rename_transaction_capture_events_task(order_event_model):
    events = order_event_model.objects.filter(
        type="transaction_capture_requested"
    ).order_by("pk")

    for ids in queryset_in_batches(events):
        qs = order_event_model.objects.filter(pk__in=ids)
        update_type_to_transaction_charge_requested(qs)


def rename_order_events(apps, _schema_editor):
    OrderEvent = apps.get_model("order", "OrderEvent")
    order_events_rename_transaction_capture_events_task(OrderEvent)
    order_events_rename_transaction_void_events_task(OrderEvent)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0162_order_granted_refund"),
    ]
    operations = [
        migrations.RunPython(
            rename_order_events, reverse_code=migrations.RunPython.noop
        ),
    ]
