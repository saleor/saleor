import logging
import uuid
from datetime import datetime

import pytz
from django.conf import settings
from django.db.models import OuterRef, Q, Subquery

from ..celeryconf import app
from ..channel.models import Channel
from ..checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from ..checkout.models import Checkout
from ..payment.models import TransactionEvent, TransactionItem
from ..plugins.manager import get_plugins_manager
from . import PaymentError, TransactionAction, TransactionEventType
from .gateway import request_cancelation_action, request_refund_action

logger = logging.getLogger(__name__)


def checkouts_with_funds_to_release():
    """Fetch checkouts that are ready release the funds.

    Fetch checkouts with the funds where the last modification was more than defined
    TTL ago. Exclude the checkouts with payment statuses which define that the
    checkout doesn't have any processed funds.
    """
    expired_checkouts_time = (
        datetime.now(pytz.UTC) - settings.CHECKOUT_TTL_BEFORE_RELEASING_FUNDS
    )

    return Checkout.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).filter(
        Q(
            automatically_refundable=True,
            last_change__lt=expired_checkouts_time,
            last_transaction_modified_at__lt=expired_checkouts_time,
        )
        & (
            ~Q(authorize_status=CheckoutAuthorizeStatus.NONE)
            | ~Q(charge_status=CheckoutChargeStatus.NONE)
        )
    )


@app.task
def transaction_release_funds_for_checkout_task():
    CHECKOUT_BATCH_SIZE = int(settings.CHECKOUT_BATCH_FOR_RELEASING_FUNDS)
    TRANSACTION_BATCH_SIZE = int(settings.TRANSACTION_BATCH_FOR_RELEASING_FUNDS)

    # Fetch checkouts that are ready to release funds
    checkouts = checkouts_with_funds_to_release().order_by("last_change")
    checkouts_data = list(
        checkouts.values_list("pk", "channel_id")[:CHECKOUT_BATCH_SIZE]
    )
    checkout_pks = [pk for pk, _ in checkouts_data]
    checkout_channel_ids = [channel_id for _, channel_id in checkouts_data]
    channel_map = (
        Channel.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(id__in=checkout_channel_ids)
        .in_bulk()
    )
    if checkout_pks:
        transaction_events = TransactionEvent.objects.filter(
            transaction_id=OuterRef("pk"),
        ).order_by("-created_at")

        checkout_subquery = Checkout.objects.filter(pk=OuterRef("checkout_id"))
        # Fetch transactions for checkouts that are ready to release funds.
        # Select_related app as, this will be used to trigger the proper webhook
        # Annotate the last event for each transaction to exclude the transactions that
        # were already processed
        transactions = (
            TransactionItem.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .select_related("app")
            .annotate(last_event_type=Subquery(transaction_events.values("type")[:1]))
            .annotate(channel_id=Subquery(checkout_subquery.values("channel_id")[:1]))
            .filter(
                Q(checkout_id__in=checkout_pks, order_id=None)
                & ~Q(
                    last_event_type__in=[
                        TransactionEventType.REFUND_REQUEST,
                        TransactionEventType.CANCEL_REQUEST,
                    ]
                )
            )[:TRANSACTION_BATCH_SIZE]
        )
        transactions_with_cancel_request_events = []
        transactions_with_charge_request_events = []

        for transaction in transactions:
            # If transaction is authorized we need to trigger the cancel event
            if transaction.authorized_value:
                event = TransactionEvent(
                    amount_value=transaction.authorized_value,
                    currency=transaction.currency,
                    type=TransactionEventType.CANCEL_REQUEST,
                    transaction_id=transaction.id,
                    idempotency_key=str(uuid.uuid4()),
                )
                transactions_with_cancel_request_events.append((transaction, event))

            # If transaction is charged we need to trigger the refund event
            if transaction.charged_value:
                event = TransactionEvent(
                    amount_value=transaction.charged_value,
                    currency=transaction.currency,
                    type=TransactionEventType.REFUND_REQUEST,
                    transaction_id=transaction.id,
                    idempotency_key=str(uuid.uuid4()),
                )
                transactions_with_charge_request_events.append((transaction, event))

        if (
            transactions_with_charge_request_events
            or transactions_with_cancel_request_events
        ):
            TransactionEvent.objects.bulk_create(
                [event for _tr, event in transactions_with_cancel_request_events]
                + [event for _tr, event in transactions_with_charge_request_events]
            )
            manager = get_plugins_manager(allow_replica=True)
            for transaction, event in transactions_with_cancel_request_events:
                channel_slug = channel_map[transaction.channel_id].slug
                try:
                    request_cancelation_action(
                        request_event=event,
                        cancel_value=event.amount_value,
                        action=TransactionAction.CANCEL,
                        channel_slug=channel_slug,
                        user=None,
                        app=None,
                        transaction=transaction,
                        manager=manager,
                    )
                except PaymentError as e:
                    logger.warning(
                        "Unable to cancel transaction %s. %s",
                        transaction.token,
                        str(e),
                    )
            for transaction, event in transactions_with_charge_request_events:
                channel_slug = channel_map[transaction.channel_id].slug
                try:
                    request_refund_action(
                        request_event=event,
                        refund_value=event.amount_value,
                        channel_slug=channel_slug,
                        user=None,
                        app=None,
                        transaction=transaction,
                        manager=manager,
                    )
                except PaymentError as e:
                    logger.warning(
                        "Unable to refund transaction %s. %s",
                        transaction.token,
                        str(e),
                    )
