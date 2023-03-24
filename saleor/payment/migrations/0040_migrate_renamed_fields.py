from django.db import migrations
from django.db.models import F, Q, QuerySet


def transaction_item_migrate_type_to_name(qs: QuerySet):
    qs.update(name=F("type"))


def transaction_item_migrate_type_to_name_task(transaction_item):
    qs = transaction_item.objects.filter(
        (Q(name__isnull=True) & Q(type__isnull=False)) | (Q(name="") & ~Q(type=""))
    ).order_by("-pk")

    transaction_item_migrate_type_to_name(qs)


def transaction_item_migrate_reference_to_psp_reference(qs: QuerySet):
    qs.update(psp_reference=F("reference"))


def transaction_item_migrate_reference_to_psp_reference_task(transaction_item):
    qs = transaction_item.objects.filter(psp_reference__isnull=True).order_by("-pk")

    transaction_item_migrate_reference_to_psp_reference(qs)


def transaction_item_migrate_voided_to_canceled(qs: QuerySet):
    qs.update(canceled_value=F("voided_value"))


def transaction_item_migrate_voided_to_canceled_task(transaction_item):
    qs = transaction_item.objects.filter(~Q(canceled_value=F("voided_value"))).order_by(
        "-pk"
    )

    transaction_item_migrate_voided_to_canceled(qs)


def transaction_event_migrate_name_to_message(qs: QuerySet):
    qs.update(message=F("name"))


def transaction_event_migrate_name_to_message_task(transaction_event):
    qs = transaction_event.objects.filter(
        (Q(message__isnull=True) & Q(name__isnull=False))
        | (Q(message="") & ~Q(name=""))
    ).order_by("-pk")

    transaction_event_migrate_name_to_message(qs)


def transaction_event_migrate_reference_to_psp_reference(qs: QuerySet):
    qs.update(psp_reference=F("reference"))


def transaction_event_migrate_reference_to_psp_reference_task(transaction_event):
    qs = transaction_event.objects.filter(~Q(psp_reference=F("reference"))).order_by(
        "-pk"
    )

    transaction_event_migrate_reference_to_psp_reference(qs)


def migrate_data_for_renamed_fields(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")
    TransactionEvent = apps.get_model("payment", "TransactionEvent")
    transaction_event_migrate_name_to_message_task(TransactionEvent)
    transaction_event_migrate_reference_to_psp_reference_task(TransactionEvent)
    transaction_item_migrate_reference_to_psp_reference_task(TransactionItem)
    transaction_item_migrate_type_to_name_task(TransactionItem)
    transaction_item_migrate_voided_to_canceled_task(TransactionItem)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0039_transactionevent_currency"),
    ]

    operations = [
        migrations.RunPython(migrate_data_for_renamed_fields, migrations.RunPython.noop)
    ]
