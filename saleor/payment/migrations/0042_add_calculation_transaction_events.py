from decimal import Decimal

from django.db import migrations
from django.db.models import F, Q, OuterRef, Subquery, Func, Exists


def create_transaction_events(apps, schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")
    TransactionEvent = apps.get_model("payment", "TransactionEvent")
    create_event_for_authorized(TransactionItem, TransactionEvent)
    create_event_for_charged(TransactionItem, TransactionEvent)
    create_event_for_refunded(TransactionItem, TransactionEvent)
    create_event_for_canceled(TransactionItem, TransactionEvent)


def _create_transaction_events(TransactionEvent, transactions_qs, type):
    transaction_events = []
    for pk, amount, amount_sum, currency in transactions_qs:
        amount_sum = 0 if not amount_sum else amount_sum
        if amount > amount_sum:
            transaction_events.append(
                TransactionEvent(
                    transaction_id=pk,
                    type=type,
                    amount_value=amount - amount_sum,
                    currency=currency,
                    include_in_calculations=True,
                    message="Manual adjustment of the transaction.",
                )
            )
    if transaction_events:
        TransactionEvent.objects.bulk_create(transaction_events)


def _get_events(TransactionEvent, type):
    return (
        TransactionEvent.objects.filter(
            transaction=OuterRef("pk"), type=type, include_in_calculations=True
        )
        .annotate(amount_sum=Func(F("amount_value"), function="Sum"))
        .values("amount_sum")
    )


def _update_all_authorized_events(TransactionItem, TransactionEvent):
    authorized_value = TransactionItem.objects.filter(
        pk=OuterRef("transaction")
    ).values("authorized_value")

    TransactionEvent.objects.filter(
        (Q(type="authorization_success") | Q(type="authorization_adjustment"))
        & Q(include_in_calculations=True)
    ).annotate(authorized_value=Subquery(authorized_value)).update(
        amount_value=F("authorized_value")
    )


def create_event_for_authorized(TransactionItem, TransactionEvent):
    transaction_events = []
    authorize_events = TransactionEvent.objects.filter(
        Q(transaction=OuterRef("pk"))
        & (Q(type="authorization_success") | Q(type="authorization_adjustment"))
        & Q(include_in_calculations=True)
    )
    authorized_transactions_without_events = TransactionItem.objects.filter(
        ~Q(authorized_value=Decimal(0)),
        ~Exists(authorize_events),
    ).values_list("id", "authorized_value", "currency")
    for pk, amount, currency in authorized_transactions_without_events:
        transaction_events.append(
            TransactionEvent(
                transaction_id=pk,
                type="authorization_success",
                amount_value=amount,
                currency=currency,
                include_in_calculations=True,
                message="Manual adjustment of the transaction.",
            )
        )
    if transaction_events:
        TransactionEvent.objects.bulk_create(transaction_events)

    _update_all_authorized_events(TransactionItem, TransactionEvent)


def create_event_for_charged(TransactionItem, TransactionEvent):
    type = "charge_success"
    events = _get_events(TransactionEvent, type)
    charged_transactions = (
        TransactionItem.objects.filter(~Q(charged_value=Decimal(0)))
        .annotate(amount_sum=Subquery(events))
        .values_list("id", "charged_value", "amount_sum", "currency")
    )
    _create_transaction_events(TransactionEvent, charged_transactions, type)


def create_event_for_refunded(TransactionItem, TransactionEvent):
    type = "refund_success"
    events = _get_events(TransactionEvent, type)
    refunded_transactions = (
        TransactionItem.objects.filter(~Q(refunded_value=Decimal(0)))
        .annotate(amount_sum=Subquery(events))
        .values_list("id", "refunded_value", "amount_sum", "currency")
    )
    _create_transaction_events(TransactionEvent, refunded_transactions, type)


def create_event_for_canceled(TransactionItem, TransactionEvent):
    type = "cancel_success"
    events = _get_events(TransactionEvent, type)
    canceled_transactions = (
        TransactionItem.objects.filter(~Q(canceled_value=Decimal(0)))
        .annotate(amount_sum=Subquery(events))
        .values_list("id", "canceled_value", "amount_sum", "currency")
    )
    _create_transaction_events(TransactionEvent, canceled_transactions, type)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0041_migrate_renamed_fields_transaction_event"),
    ]

    operations = [
        migrations.RunPython(create_transaction_events, migrations.RunPython.noop),
    ]
