import logging
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
    now = datetime.now(pytz.UTC)

    return Checkout.objects.filter(
        (
            Q(automatically_refundable=True)
            & Q(last_change__lt=now - settings.CHECKOUT_TTL_BEFORE_RELEASING_FUNDS)
            & Q(
                last_transaction_modified_at__lt=now
                - settings.CHECKOUT_TTL_BEFORE_RELEASING_FUNDS
            )
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

    checkouts = checkouts_with_funds_to_release().order_by("last_change")
    checkout_pks = checkouts.values_list("pk", flat=True)[:CHECKOUT_BATCH_SIZE]
    if checkout_pks:
        transaction_events = TransactionEvent.objects.filter(
            transaction_id=OuterRef("pk"),
        ).order_by("-created_at")

        checkout_subquery = Checkout.objects.filter(
            pk=OuterRef("checkout_id")
        ).annotate(
            channel_slug=Subquery(
                Channel.objects.filter(pk=OuterRef("channel_id")).values("slug")[:1]
            )
        )
        transactions = (
            TransactionItem.objects.select_related("app")
            .annotate(last_event_type=Subquery(transaction_events.values("type")[:1]))
            .annotate(
                channel_slug=Subquery(checkout_subquery.values("channel_slug")[:1])
            )
            .filter(checkout_id__in=checkout_pks, order_id=None)[
                :TRANSACTION_BATCH_SIZE
            ]
        )
        transactions_with_cancel_request_events = []
        transactions_with_charge_request_events = []

        for transaction in transactions:
            if transaction.last_event_type in [
                TransactionEventType.REFUND_REQUEST,
                TransactionEventType.CANCEL_REQUEST,
            ]:
                continue
            if transaction.authorized_value:
                event = TransactionEvent(
                    amount_value=transaction.authorized_value,
                    currency=transaction.currency,
                    type=TransactionEventType.CANCEL_REQUEST,
                    transaction_id=transaction.id,
                )
                transactions_with_cancel_request_events.append((transaction, event))
            if transaction.charged_value:
                event = TransactionEvent(
                    amount_value=transaction.charged_value,
                    currency=transaction.currency,
                    type=TransactionEventType.REFUND_REQUEST,
                    transaction_id=transaction.id,
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
            manager = get_plugins_manager()
            for transaction, event in transactions_with_cancel_request_events:
                action_kwargs = {
                    "channel_slug": transaction.channel_slug,
                    "user": None,
                    "app": None,
                    "transaction": transaction,
                    "manager": manager,
                }
                try:
                    request_cancelation_action(
                        **action_kwargs,
                        request_event=event,
                        cancel_value=event.amount_value,
                        action=TransactionAction.CANCEL,
                    )
                except PaymentError as e:
                    logger.warning(
                        "Unable to cancel transaction %s. %s",
                        transaction.token,
                        str(e),
                    )
            for transaction, event in transactions_with_charge_request_events:
                action_kwargs = {
                    "channel_slug": transaction.channel_slug,
                    "user": None,
                    "app": None,
                    "transaction": transaction,
                    "manager": manager,
                }
                try:
                    request_refund_action(
                        **action_kwargs,
                        request_event=event,
                        refund_value=event.amount_value,
                    )
                except PaymentError as e:
                    logger.warning(
                        "Unable to refund transaction %s. %s",
                        transaction.token,
                        str(e),
                    )
