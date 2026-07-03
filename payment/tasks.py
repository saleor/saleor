import datetime
import logging
import uuid

import graphene
from django.conf import settings
from django.db import transaction
from django.db.models import DateTimeField, Exists, ExpressionWrapper, OuterRef, Q

from ..celeryconf import app
from ..channel.models import Channel
from ..checkout import CheckoutAuthorizeStatus
from ..checkout.models import Checkout
from ..core.db.connection import allow_writer
from ..payment.models import TransactionEvent, TransactionItem
from ..plugins.manager import get_plugins_manager
from . import PaymentError, TransactionAction, TransactionEventType
from .gateway import request_cancelation_action, request_refund_action

logger = logging.getLogger(__name__)


def transactions_to_release_funds():
    """Fetch transactions for checkouts eligible for automatic refunds.

    The function retrieves checkouts that are automatically refundable and have exceeded the
    predefined TTL. It then fetches related transactions that are authorized or charged,
    ready for fund release.
    """
    now = datetime.datetime.now(datetime.UTC)
    channels = (
        Channel.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .annotate(
            last_transaction_modified_at=ExpressionWrapper(
                OuterRef(
                    "last_transaction_modified_at",
                ),
                output_field=DateTimeField(),
            )
        )
        .filter(
            Q(release_funds_for_expired_checkouts=True)
            & Q(
                checkout_ttl_before_releasing_funds__lt=now - OuterRef("last_change")  # type: ignore[operator]
            )
            & (
                Q(last_transaction_modified_at__isnull=True)
                | Q(
                    checkout_ttl_before_releasing_funds__lt=now
                    - OuterRef("last_transaction_modified_at")  # type: ignore[operator]
                )
            )
            & Q(pk=OuterRef("channel_id"))
            & (
                Q(checkout_release_funds_cut_off_date__isnull=True)
                | Q(checkout_release_funds_cut_off_date__lt=OuterRef("created_at"))
            )
        )
    )

    checkouts = Checkout.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(
        Exists(channels),
        created_at__gt=now - datetime.timedelta(days=365),
        automatically_refundable=True,
        authorize_status__in=[
            CheckoutAuthorizeStatus.PARTIAL,
            CheckoutAuthorizeStatus.FULL,
        ],
    )

    # Fetch transactions for checkouts that are ready to release funds.
    transactions = (
        TransactionItem.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).filter(
            Q(
                Exists(checkouts.filter(pk=OuterRef("checkout_id"))),
                order_id=None,
                last_refund_success=True,
            )
            & (Q(authorized_value__gt=0) | Q(charged_value__gt=0))
        )
    ).order_by("created_at")
    return transactions


@app.task
@allow_writer()
def transaction_release_funds_for_checkout_task():
    TRANSACTION_BATCH_SIZE = int(settings.TRANSACTION_BATCH_FOR_RELEASING_FUNDS)

    # Fetch transactions that are ready to release funds
    transactions = transactions_to_release_funds().order_by("modified_at")
    transactions_data = list(
        transactions.values_list("pk", "checkout_id")[:TRANSACTION_BATCH_SIZE]
    )
    transaction_pks = [pk for pk, _checkout_id in transactions_data]
    checkout_ids = [checkout_id for _, checkout_id in transactions_data]

    checkouts_data = Checkout.objects.filter(pk__in=checkout_ids).values_list(
        "pk", "channel_id"
    )
    checkout_channel_ids = {channel_id for _, channel_id in checkouts_data}
    channels_in_bulk = (
        Channel.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(id__in=checkout_channel_ids)
        .in_bulk()
    )
    checkout_id_to_channel = {
        checkout_id: channels_in_bulk[channel_id]
        for checkout_id, channel_id in checkouts_data
    }
    if transaction_pks:
        # Select_related app as, this will be used to trigger the proper webhook.
        transactions = TransactionItem.objects.filter(
            pk__in=transaction_pks,
            order_id=None,  # type: ignore[misc]
        ).select_related("app")
        transactions_with_cancel_request_events = []
        transactions_with_charge_request_events = []

        for transaction_item in transactions:
            # If transaction is authorized we need to trigger the cancel event
            if transaction_item.authorized_value:
                event = TransactionEvent(
                    amount_value=transaction_item.authorized_value,
                    currency=transaction_item.currency,
                    type=TransactionEventType.CANCEL_REQUEST,
                    transaction_id=transaction_item.id,
                    idempotency_key=str(uuid.uuid4()),
                )
                transactions_with_cancel_request_events.append(
                    (transaction_item, event)
                )

            # If transaction is charged we need to trigger the refund event
            if transaction_item.charged_value:
                event = TransactionEvent(
                    amount_value=transaction_item.charged_value,
                    currency=transaction_item.currency,
                    type=TransactionEventType.REFUND_REQUEST,
                    transaction_id=transaction_item.id,
                    idempotency_key=str(uuid.uuid4()),
                )
                transactions_with_charge_request_events.append(
                    (transaction_item, event)
                )

        if (
            transactions_with_charge_request_events
            or transactions_with_cancel_request_events
        ):
            with transaction.atomic():
                TransactionEvent.objects.bulk_create(
                    [event for _tr, event in transactions_with_cancel_request_events]
                    + [event for _tr, event in transactions_with_charge_request_events]
                )
                # Mark transactions as not refundable to avoid multiple automatic
                # refund requests
                transactions.update(last_refund_success=False)

            manager = get_plugins_manager(allow_replica=True)
            for transaction_item, event in transactions_with_cancel_request_events:
                channel = checkout_id_to_channel[transaction_item.checkout_id]  # type: ignore[index]
                logger.info(
                    "Releasing funds for transaction %s - canceling",
                    transaction_item.token,
                    extra={
                        "transactionId": graphene.Node.to_global_id(
                            "TransactionItem", transaction_item.pk
                        )
                    },
                )
                try:
                    request_cancelation_action(
                        request_event=event,
                        cancel_value=event.amount_value,
                        action=TransactionAction.CANCEL,
                        channel_slug=channel.slug,
                        user=None,
                        app=None,
                        transaction=transaction_item,
                        manager=manager,
                    )
                except PaymentError as e:
                    logger.warning(
                        "Unable to cancel transaction %s. %s",
                        transaction_item.token,
                        str(e),
                    )
            for transaction_item, event in transactions_with_charge_request_events:
                channel = checkout_id_to_channel[transaction_item.checkout_id]  # type: ignore[index]
                logger.info(
                    "Releasing funds for transaction %s - refunding",
                    transaction_item.token,
                    extra={
                        "transactionId": graphene.Node.to_global_id(
                            "TransactionItem", transaction_item.pk
                        )
                    },
                )
                try:
                    request_refund_action(
                        request_event=event,
                        refund_value=event.amount_value,
                        channel_slug=channel.slug,
                        user=None,
                        app=None,
                        transaction=transaction_item,
                        manager=manager,
                    )
                except PaymentError as e:
                    logger.warning(
                        "Unable to refund transaction %s. %s",
                        transaction_item.token,
                        str(e),
                    )
        else:
            logger.warning("No transactions to release funds.")
