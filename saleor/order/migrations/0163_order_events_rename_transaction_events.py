from django.db import migrations

BATCH_SIZE = 1000


def queryset_in_batches(qs):
    def batch_ids():
        length = len(ids)
        for index in range(0, length, BATCH_SIZE):
            yield ids[index : min(index + BATCH_SIZE, length)]

    ids = qs.values_list("pk", flat=True)
    for ids_batch in batch_ids():
        yield ids_batch


def update_type_to_transaction_cancel_requested(qs):
    qs.update(type="transaction_cancel_requested")


def order_events_rename_transaction_void_events(OrderEvent):
    query_set = OrderEvent.objects.filter(type="transaction_void_requested").order_by(
        "-pk"
    )

    for ids_batch in queryset_in_batches(query_set):
        qs = OrderEvent.objects.filter(pk__in=ids_batch)
        update_type_to_transaction_cancel_requested(qs)


def update_type_to_transaction_charge_requested(qs):
    qs.update(type="transaction_charge_requested")


def order_events_rename_transaction_capture_events(OrderEvent):
    query_set = OrderEvent.objects.filter(
        type="transaction_capture_requested"
    ).order_by("-pk")

    for ids_batch in queryset_in_batches(query_set):
        qs = OrderEvent.objects.filter(pk__in=ids_batch)
        update_type_to_transaction_charge_requested(qs)


def rename_order_events(apps, _schema_editor):
    OrderEvent = apps.get_model("order", "OrderEvent")
    order_events_rename_transaction_capture_events(OrderEvent)
    order_events_rename_transaction_void_events(OrderEvent)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0162_order_granted_refund"),
    ]
    operations = [
        migrations.RunPython(
            rename_order_events, reverse_code=migrations.RunPython.noop
        ),
    ]
