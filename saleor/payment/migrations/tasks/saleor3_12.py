from decimal import Decimal

from django.db.models import F, Q, Case, OuterRef, Subquery, Exists, Func, When

from ....celeryconf import app
from ...models import TransactionEvent, TransactionItem

# Batch size of 1000 is about ~20MB of memory usage in task
BATCH_SIZE = 1000


def _create_transaction_events(transactions_qs, type):
    transaction_events = []
    for pk, amount, amount_sum, currency in transactions_qs:
        amount_sum = 0 if not amount_sum else amount_sum
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

    del transaction_events


def _get_events(type):
    return (
        TransactionEvent.objects.filter(
            transaction=OuterRef("pk"), type=type, include_in_calculations=True
        )
        .annotate(amount_sum=Func(F("amount_value"), function="Sum"))
        .values("amount_sum")
    )


@app.task
def create_event_for_authorized():
    transaction_events = []
    authorize_events = TransactionEvent.objects.filter(
        Q(transaction=OuterRef("pk"))
        & (Q(type="authorization_success") | Q(type="authorization_adjustment"))
        & Q(include_in_calculations=True)
    )
    qs = TransactionItem.objects.filter(
        ~Q(authorized_value=Decimal(0)),
        ~Exists(authorize_events),
    )

    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if ids:
        authorized_transactions_without_events = qs.filter(pk__in=ids).values_list(
            "id", "authorized_value", "currency"
        )

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

        del transaction_events
        del ids

        create_event_for_authorized.delay()


@app.task
def create_event_for_charged():
    type = "charge_success"
    events = _get_events(type)
    qs = (
        TransactionItem.objects.filter(~Q(charged_value=Decimal(0)))
        .annotate(
            amount_sum_temp=Subquery(events),
            amount_sum=Case(
                When(amount_sum_temp__isnull=True, then=Decimal(0)),
                default=F("amount_sum_temp"),
            ),
        )
        .filter(charged_value__gt=F("amount_sum"))
    )

    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if ids:
        transactions = qs.filter(pk__in=ids).values_list(
            "id", "charged_value", "amount_sum", "currency"
        )
        _create_transaction_events(transactions, type)

        del ids

        create_event_for_charged.delay()


@app.task
def create_event_for_refunded():
    type = "refund_success"
    events = _get_events(type)
    qs = (
        TransactionItem.objects.filter(~Q(refunded_value=Decimal(0)))
        .annotate(
            amount_sum_temp=Subquery(events),
            amount_sum=Case(
                When(amount_sum_temp__isnull=True, then=Decimal(0)),
                default=F("amount_sum_temp"),
            ),
        )
        .filter(refunded_value__gt=F("amount_sum"))
    )

    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if ids:
        transactions = qs.filter(pk__in=ids).values_list(
            "id", "refunded_value", "amount_sum", "currency"
        )
        _create_transaction_events(transactions, type)

        del ids

        create_event_for_refunded.delay()


@app.task
def create_event_for_canceled():
    type = "cancel_success"
    events = _get_events(type)
    # voided_value instead of canceled_value cause some data may not be migrated yet
    qs = (
        TransactionItem.objects.filter(~Q(voided_value=Decimal(0)))
        .annotate(
            amount_sum_temp=Subquery(events),
            amount_sum=Case(
                When(amount_sum_temp__isnull=True, then=Decimal(0)),
                default=F("amount_sum_temp"),
            ),
        )
        .filter(voided_value__gt=F("amount_sum"))
    )

    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]

    if ids:
        transactions = qs.filter(pk__in=ids).values_list(
            "id", "voided_value", "amount_sum", "currency"
        )
        _create_transaction_events(transactions, type)

        del ids

        create_event_for_canceled.delay()


@app.task
def transaction_item_migrate_type_to_name():
    qs = TransactionItem.objects.filter(Q(name__isnull=True) | Q(name=""))
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]

    if ids:
        qs.filter(pk__in=ids).update(name=F("type"))

        del ids

        transaction_item_migrate_type_to_name.delay()


@app.task
def transaction_item_migrate_reference_to_psp_reference():
    qs = TransactionItem.objects.filter(psp_reference__isnull=True)
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]

    if ids:
        qs.filter(pk__in=ids).update(psp_reference=F("reference"))

        del ids

        transaction_item_migrate_reference_to_psp_reference.delay()


@app.task
def transaction_item_migrate_voided_to_canceled():
    qs = TransactionItem.objects.filter(~Q(canceled_value=F("voided_value")))
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]

    if ids:
        qs.filter(pk__in=ids).update(canceled_value=F("voided_value"))

        del ids

        transaction_item_migrate_voided_to_canceled.delay()


@app.task
def transaction_event_migrate_name_to_message():
    qs = TransactionEvent.objects.filter(
        (Q(message__isnull=True) & Q(name__isnull=False))
        | (Q(message="") & ~Q(name=""))
    )
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]

    if ids:
        qs.filter(pk__in=ids).update(message=F("name"))

        del ids

        transaction_event_migrate_name_to_message.delay()


@app.task
def transaction_event_migrate_reference_to_psp_reference():
    qs = TransactionEvent.objects.filter(~Q(psp_reference=F("reference")))
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]

    if ids:
        qs.filter(pk__in=ids).update(psp_reference=F("reference"))

        del ids

        transaction_event_migrate_reference_to_psp_reference.delay()


@app.task
def set_default_currency_for_transaction_event_task():
    transaction_item = TransactionItem.objects.filter(
        pk=OuterRef("transaction")
    ).values("currency")
    qs = TransactionEvent.objects.filter(currency__isnull=True)
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]

    if ids:
        qs.filter(pk__in=ids).annotate(
            transaction_currency=Subquery(transaction_item)
        ).update(currency=F("transaction_currency"))

        del ids

        set_default_currency_for_transaction_event_task.delay()
