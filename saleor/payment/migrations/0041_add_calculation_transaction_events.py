from decimal import Decimal

from django.db import migrations


def create_transaction_events(apps, schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")
    TransactionEvent = apps.get_model("payment", "TransactionEvent")
    create_event_for_authorized(TransactionItem, TransactionEvent)
    create_event_for_charged(TransactionItem, TransactionEvent)
    create_event_for_refunded(TransactionItem, TransactionEvent)
    create_event_for_canceled(TransactionItem, TransactionEvent)


def create_event_for_authorized(TransactionItem, TransactionEvent):
    transaction_events = []
    authorized_transactions = TransactionItem.objects.exclude(
        authorized_value=Decimal(0)
    ).values_list(
        "id",
        "authorized_value",
        "charged_value",
        "refunded_value",
        "canceled_value",
        "currency",
    )
    for (
        pk,
        authorized_value,
        charged_value,
        refunded_value,
        canceled_value,
        currency,
    ) in authorized_transactions:
        transaction_events.append(
            TransactionEvent(
                transaction_id=pk,
                type="authorization_success",
                amount_value=authorized_value
                + charged_value
                + refunded_value
                + canceled_value,
                currency=currency,
                include_in_calculations=True,
                message="Manual adjustment of the transaction.",
            )
        )
    if transaction_events:
        TransactionEvent.objects.bulk_create(transaction_events)


def create_event_for_charged(TransactionItem, TransactionEvent):
    transaction_events = []
    charged_transactions = TransactionItem.objects.exclude(
        charged_value=Decimal(0)
    ).values_list("id", "charged_value", "refunded_value", "currency")
    for pk, charged_value, refunded_value, currency in charged_transactions:
        transaction_events.append(
            TransactionEvent(
                transaction_id=pk,
                type="charge_success",
                amount_value=charged_value + refunded_value,
                currency=currency,
                include_in_calculations=True,
                message="Manual adjustment of the transaction.",
            )
        )
    if transaction_events:
        TransactionEvent.objects.bulk_create(transaction_events)


def create_event_for_refunded(TransactionItem, TransactionEvent):
    transaction_events = []
    refunded_transactions = TransactionItem.objects.exclude(
        refunded_value=Decimal(0)
    ).values_list("id", "refunded_value", "currency")
    for pk, amount, currency in refunded_transactions:
        transaction_events.append(
            TransactionEvent(
                transaction_id=pk,
                type="refund_success",
                amount_value=amount,
                currency=currency,
                include_in_calculations=True,
                message="Manual adjustment of the transaction.",
            )
        )
    if transaction_events:
        TransactionEvent.objects.bulk_create(transaction_events)


def create_event_for_canceled(TransactionItem, TransactionEvent):
    transaction_events = []
    canceled_transactions = TransactionItem.objects.exclude(
        canceled_value=Decimal(0)
    ).values_list("id", "canceled_value", "currency")
    for pk, amount, currency in canceled_transactions:
        transaction_events.append(
            TransactionEvent(
                transaction_id=pk,
                type="cancel_success",
                amount_value=amount,
                currency=currency,
                include_in_calculations=True,
                message="Manual adjustment of the transaction.",
            )
        )
    if transaction_events:
        TransactionEvent.objects.bulk_create(transaction_events)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0040_auto_20220922_1146"),
    ]

    operations = [
        migrations.RunPython(create_transaction_events, migrations.RunPython.noop),
    ]
