from decimal import Decimal

from django.db import migrations
from django.db.models import Case, Exists, F, Func, OuterRef, Q, Subquery, When


def create_transaction_events(transaction_event, transactions_qs, type):
    transaction_events = []
    for pk, amount, amount_sum, currency in transactions_qs:
        amount_sum = 0 if not amount_sum else amount_sum
        transaction_events.append(
            transaction_event(
                transaction_id=pk,
                type=type,
                amount_value=amount - amount_sum,
                currency=currency,
                include_in_calculations=True,
                message="Manual adjustment of the transaction.",
            )
        )
    if transaction_events:
        transaction_event.objects.bulk_create(transaction_events)


def _get_events(transaction_event, type):
    return (
        transaction_event.objects.filter(
            transaction=OuterRef("pk"), type=type, include_in_calculations=True
        )
        .annotate(amount_sum=Func(F("amount_value"), function="Sum"))
        .values("amount_sum")
    )


def create_event_for_authorized(transaction_event, transaction_qs):
    transaction_events = []

    for pk, amount, currency in transaction_qs:
        transaction_events.append(
            transaction_event(
                transaction_id=pk,
                type="authorization_success",
                amount_value=amount,
                currency=currency,
                include_in_calculations=True,
                message="Manual adjustment of the transaction.",
            )
        )
    if transaction_events:
        transaction_event.objects.bulk_create(transaction_events)


def create_event_for_authorized_task(transaction_item, transaction_event):
    authorize_events = transaction_event.objects.filter(
        Q(transaction=OuterRef("pk"))
        & (Q(type="authorization_success") | Q(type="authorization_adjustment"))
        & Q(include_in_calculations=True)
    )
    qs = (
        transaction_item.objects.filter(
            ~Q(authorized_value=Decimal(0)),
            ~Exists(authorize_events),
        )
        .order_by("-pk")
        .values_list("id", "authorized_value", "currency")
    )

    create_event_for_authorized(transaction_event, qs)


def create_event_for_charged_task(transaction_item, transaction_event):
    type = "charge_success"
    events = _get_events(transaction_event, type)
    qs = (
        (
            transaction_item.objects.filter(~Q(charged_value=Decimal(0)))
            .annotate(
                amount_sum_temp=Subquery(events),
                amount_sum=Case(
                    When(amount_sum_temp__isnull=True, then=Decimal(0)),
                    default=F("amount_sum_temp"),
                ),
            )
            .filter(charged_value__gt=F("amount_sum"))
        )
        .order_by("-pk")
        .values_list("id", "charged_value", "amount_sum", "currency")
    )

    create_transaction_events(transaction_event, qs, type)


def create_event_for_refunded_task(transaction_item, transaction_event):
    type = "refund_success"
    events = _get_events(transaction_event, type)
    qs = (
        (
            transaction_item.objects.filter(~Q(refunded_value=Decimal(0)))
            .annotate(
                amount_sum_temp=Subquery(events),
                amount_sum=Case(
                    When(amount_sum_temp__isnull=True, then=Decimal(0)),
                    default=F("amount_sum_temp"),
                ),
            )
            .filter(refunded_value__gt=F("amount_sum"))
        )
        .order_by("-pk")
        .values_list("id", "refunded_value", "amount_sum", "currency")
    )

    create_transaction_events(transaction_event, qs, type)


def create_event_for_canceled_task(transaction_item, transaction_event):
    type = "cancel_success"
    events = _get_events(transaction_event, type)
    # voided_value instead of canceled_value cause some data may not be migrated yet
    qs = (
        (
            transaction_item.objects.filter(~Q(voided_value=Decimal(0)))
            .annotate(
                amount_sum_temp=Subquery(events),
                amount_sum=Case(
                    When(amount_sum_temp__isnull=True, then=Decimal(0)),
                    default=F("amount_sum_temp"),
                ),
            )
            .filter(voided_value__gt=F("amount_sum"))
        )
        .order_by("-pk")
        .values_list("id", "voided_value", "amount_sum", "currency")
    )

    create_transaction_events(transaction_event, qs, type)


def create_transaction_events_migration(apps, schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")
    TransactionEvent = apps.get_model("payment", "TransactionEvent")

    create_event_for_authorized_task(TransactionItem, TransactionEvent)
    create_event_for_canceled_task(TransactionItem, TransactionEvent)
    create_event_for_charged_task(TransactionItem, TransactionEvent)
    create_event_for_refunded_task(TransactionItem, TransactionEvent)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0040_migrate_renamed_fields"),
    ]

    operations = [
        migrations.RunPython(
            create_transaction_events_migration, migrations.RunPython.noop
        ),
    ]
