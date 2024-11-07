import logging
from decimal import Decimal

import graphene
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from django.utils import timezone

from ..account.models import User
from ..app.models import App
from ..celeryconf import app
from ..core.db.connection import allow_writer
from ..payment.models import TransactionItem
from ..plugins.manager import get_plugins_manager
from .complete_checkout import complete_checkout
from .fetch import fetch_checkout_info, fetch_checkout_lines
from .models import Checkout, CheckoutLine
from .utils import delete_checkouts

task_logger: logging.Logger = get_task_logger(__name__)


@app.task
def delete_expired_checkouts(
    batch_size: int = 2000,
    batch_count: int = 5,
    invocation_count: int = 1,
    invocation_limit: int = 500,
) -> tuple[int, bool]:
    """Delete inactive checkouts from the database.

    Inactivity is based on the "Checkout.last_change" datetime column.

    Deletes:
    - Anonymous checkouts after 30 days of inactivity no matter if it has lines or not,
      configurable through ``settings.ANONYMOUS_CHECKOUTS_TIMEDELTA``.
    - Users checkouts after 90 days of inactivity no matter if it has lines or not,
      configurable via``settings.USER_CHECKOUTS_TIMEDELTA``.
    - All anonymous and users checkouts after 6h of inactivity
      if there are no lines associated, refer to ``settings.EMPTY_CHECKOUTS_TIMEDELTA``.

    :param batch_size: The maximum row count that can be deleted per ``DELETE FROM``
        SQL statement. Around 13.5 KB of memory will be utilized by the Celery
        worker per row, thus 2000 will be using around 27 MB.
    :param batch_count: How many batches can be executed in a single task.
        This limits how long can the task run as there may be lots of checkouts
        to delete.
    :param invocation_count: How many times the task re-triggered itself up.
    :param invocation_limit: The maximum times the task can re-trigger itself up
        in order to limit how long it may run.

    :return: A tuple containing row count deleted (int)
             and whether there is more to delete (bool).
    """
    now = timezone.now()

    expired_anonymous_checkouts = (
        Q(last_change__lt=now - settings.ANONYMOUS_CHECKOUTS_TIMEDELTA)
        & Q(email__isnull=True)
        & Q(user__isnull=True)
    )
    expired_user_checkout = Q(
        last_change__lt=now - settings.USER_CHECKOUTS_TIMEDELTA
    ) & (Q(email__isnull=False) | Q(user__isnull=False))
    empty_checkouts = Q(last_change__lt=now - settings.EMPTY_CHECKOUTS_TIMEDELTA) & ~Q(
        Exists(
            # Type ignore reason: Subquery can be used inside Exists()
            # https://github.com/typeddjango/django-stubs/issues/985
            Subquery(  # type: ignore[arg-type]
                CheckoutLine.objects.filter(checkout_id=OuterRef("pk"))
            )
        )
    )

    with_transactions = TransactionItem.objects.filter(
        Q(checkout_id=OuterRef("pk"))
        & (
            Q(authorized_value__gt=Decimal(0))
            | Q(authorize_pending_value__gt=Decimal(0))
            | Q(charged_value__gt=Decimal(0))
            | Q(charge_pending_value__gt=Decimal(0))
            | Q(refund_pending_value__gt=Decimal(0))
            | Q(cancel_pending_value__gt=Decimal(0))
        )
    )

    qs: QuerySet[Checkout] = Checkout.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(
        (empty_checkouts | expired_anonymous_checkouts | expired_user_checkout)
        & ~Q(Exists(with_transactions))
    )
    qs = qs.only("pk").order_by()[:batch_size]

    total_deleted: int = 0
    has_more: bool = True
    for _batch_number in range(batch_count):
        checkout_ids = list(qs.values_list("pk", flat=True))
        with allow_writer():
            deleted_count = delete_checkouts(checkout_ids)
        total_deleted += deleted_count

        # Stop deleting inactive checkouts if there was no match.
        if deleted_count < batch_size:
            has_more = False
            break

    if total_deleted:
        task_logger.debug("Deleted %d checkouts.", total_deleted)

    if has_more:
        if invocation_count < invocation_limit:
            # Continue deleting checkouts as there may be still more to delete.
            delete_expired_checkouts.delay(
                batch_size=batch_size,
                batch_count=batch_count,
                invocation_count=invocation_count + 1,
                invocation_limit=invocation_limit,
            )
        else:
            task_logger.warning("Invocation limit reached, aborting task")
    return total_deleted, has_more


@app.task(queue=settings.AUTOMATIC_CHECKOUT_COMPLETION_QUEUE_NAME)
@allow_writer()
def automatic_checkout_completion_task(
    checkout_pk,
    user_id,
    app_id,
):
    """Try to automatically complete the checkout.

    If any error is raised during the process, it will be caught and logged.
    """
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)
    try:
        checkout = Checkout.objects.get(pk=checkout_pk)
    except Checkout.DoesNotExist:
        return

    user = User.objects.filter(pk=user_id).first()
    app = App.objects.filter(pk=app_id).first()

    manager = get_plugins_manager(allow_replica=False)
    lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    if unavailable_variant_pks:
        checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
        not_available_variants_ids = {
            graphene.Node.to_global_id("ProductVariant", pk)
            for pk in unavailable_variant_pks
        }
        task_logger.info(
            "The automatic checkout completion not triggered, as the checkout %s "
            "contains unavailable variants: %s.",
            checkout_id,
            ", ".join(not_available_variants_ids),
            extra={
                "checkout_id": checkout_id,
                "variant_ids": not_available_variants_ids,
            },
        )
        return

    task_logger.info(
        "Automatic checkout completion triggered for checkout: %s.",
        checkout_id,
        extra={"checkout_id": checkout_id},
    )
    try:
        complete_checkout(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            payment_data={},
            store_source=False,
            user=user,
            app=app,
            is_automatic_completion=True,
        )
    except ValidationError as error:
        task_logger.warning(
            "Automatic checkout completion failed for checkout: %s.",
            checkout_id,
            extra={
                "checkout_id": checkout_id,
                "error": str(error),
            },
        )
    else:
        task_logger.info(
            "Automatic checkout completion succeeded for checkout: %s.",
            checkout_id,
            extra={"checkout_id": checkout_id},
        )
