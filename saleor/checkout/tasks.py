import datetime
import logging
from decimal import Decimal

import graphene
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, F, OuterRef, Q, QuerySet, Subquery
from django.utils import timezone

from ..account.models import User
from ..app.models import App
from ..celeryconf import app
from ..channel.models import Channel
from ..checkout import CheckoutAuthorizeStatus
from ..core.db.connection import allow_writer
from ..core.utils import get_domain
from ..payment.models import TransactionItem
from ..plugins.manager import get_plugins_manager
from ..webhook.transport.utils import get_sqs_message_group_id
from .complete_checkout import complete_checkout
from .fetch import fetch_checkout_info, fetch_checkout_lines
from .models import Checkout, CheckoutLine
from .utils import delete_checkouts

task_logger: logging.Logger = get_task_logger(__name__)

# Checkout complete might take even 3 seconds. The task is scheduled to run
# every 1 minute, so to avoid overlapping executions, the limit is set to 20.
AUTOMATIC_COMPLETION_BATCH_SIZE = 20


@app.task
@allow_writer()
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

    qs: QuerySet[Checkout] = Checkout.objects.filter(
        (empty_checkouts | expired_anonymous_checkouts | expired_user_checkout)
        & ~Q(Exists(with_transactions))
    )
    qs = qs.only("pk").order_by()[:batch_size]

    total_deleted: int = 0
    has_more: bool = True
    for _batch_number in range(batch_count):
        checkout_ids = list(qs.values_list("pk", flat=True))
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


@app.task
def trigger_automatic_checkout_completion_task():
    """Trigger automatic checkout completion for eligible checkouts.

    This task:
    - Finds checkouts that are fully authorized and ready for completion
    - Tracks the last completion attempt time to avoid repeated retries
    - Sorts by last attempt time to prioritize checkouts that haven't been tried recently
    - Includes a safety check to skip very old checkouts (older than 30 days)
    """
    now = timezone.now()
    # Don't retry checkouts older than defined threshold
    oldest_allowed_checkout = (
        now - settings.AUTOMATIC_CHECKOUT_COMPLETION_OLDEST_MODIFIED
    )

    with allow_writer():
        channels = Channel.objects.filter(
            automatically_complete_fully_paid_checkouts=True
        )
        if not channels:
            task_logger.info(
                "No channels configured for automatic checkout completion."
            )
            return

        lookup = Q()
        for channel in channels:
            # calculate threshold time for automatic completion for given channel
            delay_minutes = channel.automatic_completion_delay or 0
            threshold_time = now - datetime.timedelta(minutes=float(delay_minutes))
            kwargs = {
                "channel_id": channel.pk,
                "last_change__lt": threshold_time,
            }
            if cut_off_date := channel.automatic_completion_cut_off_date:
                kwargs["created_at__gte"] = cut_off_date
            lookup |= Q(**kwargs)

        checkouts = (
            Checkout.objects.filter(authorize_status=CheckoutAuthorizeStatus.FULL)
            .filter(
                Q(last_change__gte=oldest_allowed_checkout)
                & (Q(email__isnull=False) | Q(user__isnull=False))
                & Q(billing_address__isnull=False)
                & Q(total_gross_amount__gt=Decimal("0.0"))
            )
            .filter(lookup)
            # Sort by last attempt time (nulls first - never attempted), then by last_change
            .order_by(
                F("last_automatic_completion_attempt").asc(nulls_first=True),
                "last_change",
            )
        )

        if not checkouts:
            task_logger.info("No checkouts found for automatic completion.")

        domain = get_domain()
        for checkout in checkouts[:AUTOMATIC_COMPLETION_BATCH_SIZE]:
            automatic_checkout_completion_task.apply_async(
                args=[checkout.pk],
                kwargs={},
                headers={"MessageGroupId": get_sqs_message_group_id(domain)},
            )


@app.task(
    queue=settings.AUTOMATIC_CHECKOUT_COMPLETION_QUEUE_NAME,
    bind=True,
    default_retry_delay=60,
    retry_kwargs={"max_retries": 5},
)
@allow_writer()
def automatic_checkout_completion_task(
    self,
    checkout_pk,
    user_id=None,
    app_id=None,
):
    """Try to automatically complete the checkout.

    If any error is raised during the process, it will be caught and logged.
    """
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)
    with transaction.atomic():
        checkout = Checkout.objects.select_for_update().filter(pk=checkout_pk).first()
        if not checkout:
            return
        checkout.last_automatic_completion_attempt = timezone.now()
        checkout.save(update_fields=["last_automatic_completion_attempt"])

    user = User.objects.filter(pk=user_id).first() if user_id else None
    app = App.objects.filter(pk=app_id).first() if app_id else None

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

    if not lines:
        task_logger.info(
            "The automatic checkout completion not triggered, as the checkout %s "
            "has no lines.",
            checkout_id,
            extra={"checkout_id": checkout_id},
        )
        return

    if checkout.is_shipping_required() and (
        not checkout.shipping_method_id
        and not checkout.external_shipping_method_id
        and not checkout.collection_point_id
        and not checkout.assigned_delivery_id
    ):
        task_logger.info(
            "The automatic checkout completion not triggered, as the checkout %s "
            "has no shipping method set.",
            checkout_id,
            extra={"checkout_id": checkout_id},
        )
        return

    task_logger.info(
        "Automatic checkout completion triggered for checkout: %s.",
        checkout_id,
        extra={"checkout_id": checkout_id},
    )

    failed_error_msg = "Automatic checkout completion failed for checkout: %s."
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
            failed_error_msg,
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
