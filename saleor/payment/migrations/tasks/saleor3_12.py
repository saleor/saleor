from decimal import Decimal

from django.db.models import (
    Case,
    Exists,
    F,
    Func,
    OuterRef,
    Subquery,
    Q,
    QuerySet,
    When,
)

from ....celeryconf import app
from ...models import TransactionEvent, TransactionItem

# Batch size of 1000 is about ~20MB of memory usage in task
BATCH_SIZE = 1000


def create_transaction_events(transactions_qs, type):
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


def _get_events(type):
    return (
        TransactionEvent.objects.filter(
            transaction=OuterRef("pk"), type=type, include_in_calculations=True
        )
        .annotate(amount_sum=Func(F("amount_value"), function="Sum"))
        .values("amount_sum")
    )


def create_event_for_authorized(transaction_qs):
    transaction_events = []

    for pk, amount, currency in transaction_qs:
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


@app.task
def create_event_for_authorized_task():
    authorize_events = TransactionEvent.objects.filter(
        Q(transaction=OuterRef("pk"))
        & (Q(type="authorization_success") | Q(type="authorization_adjustment"))
        & Q(include_in_calculations=True)
    )
    qs = TransactionItem.objects.filter(
        ~Q(authorized_value=Decimal(0)),
        ~Exists(authorize_events),
    ).order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids).values_list("id", "authorized_value", "currency")

    if ids:
        create_event_for_authorized(qs)
        create_event_for_authorized_task.delay()


@app.task
def create_event_for_charged_task():
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
    ).order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids).values_list(
        "id", "charged_value", "amount_sum", "currency"
    )

    if ids:
        create_transaction_events(qs, type)
        create_event_for_charged_task.delay()


@app.task
def create_event_for_refunded_task():
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
    ).order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids).values_list(
        "id", "refunded_value", "amount_sum", "currency"
    )

    if ids:
        create_transaction_events(qs, type)
        create_event_for_refunded_task.delay()


@app.task
def create_event_for_canceled_task():
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
    ).order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids).values_list(
        "id", "voided_value", "amount_sum", "currency"
    )

    if ids:
        create_transaction_events(qs, type)
        create_event_for_canceled_task.delay()


def transaction_item_migrate_type_to_name(qs: QuerySet):
    qs.update(name=F("type"))


@app.task
def transaction_item_migrate_type_to_name_task():
    qs = TransactionItem.objects.filter(
        (Q(name__isnull=True) & Q(type__isnull=False)) | (Q(name="") & ~Q(type=""))
    ).order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids)

    if ids:
        transaction_item_migrate_type_to_name(qs)
        transaction_item_migrate_type_to_name_task.delay()


def transaction_item_migrate_reference_to_psp_reference(qs: QuerySet):
    qs.update(psp_reference=F("reference"))


@app.task
def transaction_item_migrate_reference_to_psp_reference_task():
    qs = TransactionItem.objects.filter(psp_reference__isnull=True).order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids)

    if ids:
        transaction_item_migrate_reference_to_psp_reference(qs)
        transaction_item_migrate_reference_to_psp_reference_task.delay()


def transaction_item_migrate_voided_to_canceled(qs: QuerySet):
    qs.update(canceled_value=F("voided_value"))


@app.task
def transaction_item_migrate_voided_to_canceled_task():
    qs = TransactionItem.objects.filter(~Q(canceled_value=F("voided_value"))).order_by(
        "-pk"
    )
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids)

    if ids:
        transaction_item_migrate_voided_to_canceled(qs)
        transaction_item_migrate_voided_to_canceled_task.delay()


def transaction_event_migrate_name_to_message(qs: QuerySet):
    qs.update(message=F("name"))


@app.task
def transaction_event_migrate_name_to_message_task():
    qs = TransactionEvent.objects.filter(
        (Q(message__isnull=True) & Q(name__isnull=False))
        | (Q(message="") & ~Q(name=""))
    ).order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids)

    if ids:
        transaction_event_migrate_name_to_message(qs)
        transaction_event_migrate_name_to_message_task.delay()


def transaction_event_migrate_reference_to_psp_reference(qs: QuerySet):
    qs.update(psp_reference=F("reference"))


@app.task
def transaction_event_migrate_reference_to_psp_reference_task():
    qs = TransactionEvent.objects.filter(~Q(psp_reference=F("reference"))).order_by(
        "-pk"
    )
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids)

    if ids:
        transaction_event_migrate_reference_to_psp_reference(qs)
        transaction_event_migrate_reference_to_psp_reference_task.delay()


def set_default_currency_for_transaction_event(qs: QuerySet):
    qs.update(currency=F("transaction_currency"))


@app.task
def set_default_currency_for_transaction_event_task():
    transaction_item = TransactionItem.objects.filter(
        pk=OuterRef("transaction")
    ).values("currency")
    qs = TransactionEvent.objects.filter(currency__isnull=True).order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids).annotate(transaction_currency=Subquery(transaction_item))

    if ids:
        set_default_currency_for_transaction_event(qs)
        set_default_currency_for_transaction_event_task.delay()
