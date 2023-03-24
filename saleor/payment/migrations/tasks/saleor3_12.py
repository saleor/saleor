from decimal import Decimal

from django.db.models import Case, Exists, F, Func, OuterRef, Q, Subquery, When

from ....celeryconf import app
from ...models import TransactionEvent, TransactionItem

# Batch size of 1000 is about ~20MB of memory usage in task
BATCH_SIZE = 1000


def _get_ids(qs, batch_size=None):
    if batch_size:
        return qs.values_list("pk", flat=True)[:batch_size]
    return qs.values_list("pk", flat=True)


def _create_transaction_events(transaction_event_class, transactions_qs, type):
    transaction_events = []
    for pk, amount, amount_sum, currency in transactions_qs:
        amount_sum = 0 if not amount_sum else amount_sum
        transaction_events.append(
            transaction_event_class(
                transaction_id=pk,
                type=type,
                amount_value=amount - amount_sum,
                currency=currency,
                include_in_calculations=True,
                message="Manual adjustment of the transaction.",
            )
        )
    if transaction_events:
        transaction_event_class.objects.bulk_create(transaction_events)


def _get_events(transaction_event_class, type):
    return (
        transaction_event_class.objects.filter(
            transaction=OuterRef("pk"), type=type, include_in_calculations=True
        )
        .annotate(amount_sum=Func(F("amount_value"), function="Sum"))
        .values("amount_sum")
    )


def create_event_for_authorized(
    transaction_item_class, transaction_event_class, batch_size=None
):
    transaction_events = []
    authorize_events = transaction_event_class.objects.filter(
        Q(transaction=OuterRef("pk"))
        & (Q(type="authorization_success") | Q(type="authorization_adjustment"))
        & Q(include_in_calculations=True)
    )
    qs = transaction_item_class.objects.filter(
        ~Q(authorized_value=Decimal(0)),
        ~Exists(authorize_events),
    )

    ids = _get_ids(qs, batch_size)
    if ids:
        authorized_transactions_without_events = qs.filter(pk__in=ids).values_list(
            "id", "authorized_value", "currency"
        )

        for pk, amount, currency in authorized_transactions_without_events:
            transaction_events.append(
                transaction_event_class(
                    transaction_id=pk,
                    type="authorization_success",
                    amount_value=amount,
                    currency=currency,
                    include_in_calculations=True,
                    message="Manual adjustment of the transaction.",
                )
            )
        if transaction_events:
            transaction_event_class.objects.bulk_create(transaction_events)


@app.task
def create_event_for_authorized_task():
    if create_event_for_authorized(TransactionItem, TransactionEvent, BATCH_SIZE):
        create_event_for_authorized_task.delay()


def create_event_for_charged(
    transaction_item_class, transaction_event_class, batch_size=None
):
    type = "charge_success"
    events = _get_events(transaction_event_class, type)
    qs = (
        transaction_item_class.objects.filter(~Q(charged_value=Decimal(0)))
        .annotate(
            amount_sum_temp=Subquery(events),
            amount_sum=Case(
                When(amount_sum_temp__isnull=True, then=Decimal(0)),
                default=F("amount_sum_temp"),
            ),
        )
        .filter(charged_value__gt=F("amount_sum"))
    )

    ids = _get_ids(qs, batch_size)
    if ids:
        transactions = qs.filter(pk__in=ids).values_list(
            "id", "charged_value", "amount_sum", "currency"
        )
        _create_transaction_events(transaction_event_class, transactions, type)

        return True
    return False


@app.task
def create_event_for_charged_task():
    if create_event_for_charged(TransactionItem, TransactionEvent, BATCH_SIZE):
        create_event_for_charged_task.delay()


def create_event_for_refunded(
    transaction_item_class, transaction_event_class, batch_size=None
):
    type = "refund_success"
    events = _get_events(transaction_event_class, type)
    qs = (
        transaction_item_class.objects.filter(~Q(refunded_value=Decimal(0)))
        .annotate(
            amount_sum_temp=Subquery(events),
            amount_sum=Case(
                When(amount_sum_temp__isnull=True, then=Decimal(0)),
                default=F("amount_sum_temp"),
            ),
        )
        .filter(refunded_value__gt=F("amount_sum"))
    )

    ids = _get_ids(qs, batch_size)
    if ids:
        transactions = qs.filter(pk__in=ids).values_list(
            "id", "refunded_value", "amount_sum", "currency"
        )
        _create_transaction_events(transaction_event_class, transactions, type)

        return True
    return False


@app.task
def create_event_for_refunded_task():
    if create_event_for_refunded(TransactionItem, TransactionEvent, BATCH_SIZE):
        create_event_for_refunded_task.delay()


def create_event_for_canceled(
    transaction_item_class, transaction_event_class, batch_size=None
):
    type = "cancel_success"
    events = _get_events(transaction_event_class, type)
    # voided_value instead of canceled_value cause some data may not be migrated yet
    qs = (
        transaction_item_class.objects.filter(~Q(voided_value=Decimal(0)))
        .annotate(
            amount_sum_temp=Subquery(events),
            amount_sum=Case(
                When(amount_sum_temp__isnull=True, then=Decimal(0)),
                default=F("amount_sum_temp"),
            ),
        )
        .filter(voided_value__gt=F("amount_sum"))
    )

    ids = _get_ids(qs, batch_size)

    if ids:
        transactions = qs.filter(pk__in=ids).values_list(
            "id", "voided_value", "amount_sum", "currency"
        )
        _create_transaction_events(transaction_event_class, transactions, type)

        return True
    return False


@app.task
def create_event_for_canceled_task():
    if create_event_for_canceled(TransactionItem, TransactionEvent, BATCH_SIZE):
        create_event_for_canceled_task.delay()


def transaction_item_migrate_type_to_name(transaction_item_class, batch_size=None):
    qs = transaction_item_class.objects.filter(
        (Q(name__isnull=True) & Q(type__isnull=False)) | (Q(name="") & ~Q(type=""))
    )
    ids = _get_ids(qs, batch_size)

    if ids:
        qs.filter(pk__in=ids).update(name=F("type"))

        return True
    return False


@app.task
def transaction_item_migrate_type_to_name_task():
    if transaction_item_migrate_type_to_name(TransactionItem, BATCH_SIZE):
        transaction_item_migrate_type_to_name_task.delay()


def transaction_item_migrate_reference_to_psp_reference(
    transaction_item_class, batch_size=None
):
    qs = transaction_item_class.objects.filter(psp_reference__isnull=True)
    ids = _get_ids(qs, batch_size)

    if ids:
        qs.filter(pk__in=ids).update(psp_reference=F("reference"))

        return True
    return False


@app.task
def transaction_item_migrate_reference_to_psp_reference_task():
    if transaction_item_migrate_reference_to_psp_reference(TransactionItem, BATCH_SIZE):
        transaction_item_migrate_reference_to_psp_reference_task.delay()


def transaction_item_migrate_voided_to_canceled(
    transaction_item_class, batch_size=None
):
    qs = transaction_item_class.objects.filter(~Q(canceled_value=F("voided_value")))
    ids = _get_ids(qs, batch_size)

    if ids:
        qs.filter(pk__in=ids).update(canceled_value=F("voided_value"))

        return True
    return False


@app.task
def transaction_item_migrate_voided_to_canceled_task():
    if transaction_item_migrate_voided_to_canceled(TransactionItem, BATCH_SIZE):
        transaction_item_migrate_voided_to_canceled_task.delay()


def transaction_event_migrate_name_to_message(transaction_event_class, batch_size=None):
    qs = transaction_event_class.objects.filter(
        (Q(message__isnull=True) & Q(name__isnull=False))
        | (Q(message="") & ~Q(name=""))
    )
    ids = _get_ids(qs, batch_size)

    if ids:
        qs.filter(pk__in=ids).update(message=F("name"))

        return True
    return False


@app.task
def transaction_event_migrate_name_to_message_task():
    if transaction_event_migrate_name_to_message(TransactionEvent, BATCH_SIZE):
        transaction_event_migrate_name_to_message_task.delay()


def transaction_event_migrate_reference_to_psp_reference(
    transaction_event_class, batch_size=None
):
    qs = transaction_event_class.objects.filter(~Q(psp_reference=F("reference")))
    ids = _get_ids(qs, batch_size)

    if ids:
        qs.filter(pk__in=ids).update(psp_reference=F("reference"))

        return True
    return False


@app.task
def transaction_event_migrate_reference_to_psp_reference_task():
    if transaction_event_migrate_reference_to_psp_reference(
        TransactionEvent, BATCH_SIZE
    ):
        transaction_event_migrate_reference_to_psp_reference_task.delay()


def set_default_currency_for_transaction_event(
    transaction_item_class, transaction_event_class, batch_size=None
):
    transaction_item = transaction_item_class.objects.filter(
        pk=OuterRef("transaction")
    ).values("currency")
    qs = transaction_event_class.objects.filter(currency__isnull=True)
    ids = _get_ids(qs, batch_size)

    if ids:
        qs.filter(pk__in=ids).annotate(
            transaction_currency=Subquery(transaction_item)
        ).update(currency=F("transaction_currency"))

        return True
    return False


@app.task
def set_default_currency_for_transaction_event_task():
    if set_default_currency_for_transaction_event(
        TransactionItem, TransactionEvent, BATCH_SIZE
    ):
        set_default_currency_for_transaction_event_task.delay()
