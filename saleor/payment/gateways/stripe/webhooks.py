import logging
from typing import Optional

from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from stripe.error import SignatureVerificationError
from stripe.stripe_object import StripeObject

from ....checkout.complete_checkout import complete_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout
from ....core.transactions import transaction_with_commit_on_errors
from ....discount.utils import fetch_active_discounts
from ....plugins.manager import get_plugins_manager
from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse
from ...models import Payment
from ...utils import create_transaction, price_from_minor_unit
from .stripe_api import construct_stripe_event

logger = logging.getLogger(__name__)


@transaction_with_commit_on_errors()
def handle_webhook(request: WSGIRequest, gateway_config: "GatewayConfig"):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    endpoint_secret = gateway_config.connection_params["webhook_secret"]
    api_key = gateway_config.connection_params["secret_api_key"]
    try:
        event = construct_stripe_event(
            api_key=api_key,
            payload=payload,
            sig_header=sig_header,
            endpoint_secret=endpoint_secret,
        )
    except ValueError as e:
        # Invalid payload
        logger.warning("Received invalid payload. %s", e)
        return HttpResponse(status=400)
    except SignatureVerificationError as e:
        # Invalid signature
        logger.warning("Invalid signature. %s", e)
        return HttpResponse(status=400)

    # Handle the event
    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        handle_successful_payment_intent(payment_intent, gateway_config)
    # TODO handle rest of the events will be added in separate PR
    # elif event.type == 'payment_method.attached':
    #     payment_method = event.data.object  # contains a stripe.PaymentMethod
    #     print('PaymentMethod was attached to a Customer!')
    # # ... handle other event types
    # else:
    #     print('Unhandled event type {}'.format(event.type))

    return HttpResponse(status=200)


def _get_payment(payment_intent_id: str) -> Optional[Payment]:
    return (
        Payment.objects.prefetch_related(
            "checkout",
        )
        .select_for_update(of=("self",))
        .filter(transactions__token=payment_intent_id, is_active=True)
        .first()
    )


def _get_checkout(payment_id: int) -> Optional[Checkout]:
    return (
        Checkout.objects.prefetch_related("payments")
        .select_for_update(of=("self",))
        .filter(payments__id=payment_id, payments__is_active=True)
        .first()
    )


def handle_successful_payment_intent(
    payment_intent: StripeObject, gateway_config: "GatewayConfig"
):
    # TODO handle successful payment intent for pending payment - separate PR
    payment = _get_payment(payment_intent.id)

    if not payment:
        logger.warning(
            "Payment for PaymentIntent %s was not found",
            payment_intent.id,
        )
        return
    if payment.order_id:
        # Order already created
        return

    checkout = None
    if payment.checkout_id:
        checkout = _get_checkout(payment.id)

    if checkout:
        # If the payment is not Auth/Capture, it means that user didn't return to the
        # storefront and we need to finalize the checkout asynchronously.
        kind = TransactionKind.AUTH
        if payment_intent.capture_method == "automatic":
            kind = TransactionKind.CAPTURE
        gateway_response = GatewayResponse(
            kind=kind,
            action_required=False,
            transaction_id=payment_intent.id,
            is_success=True,
            amount=price_from_minor_unit(
                payment_intent.amount, payment_intent.currency
            ),
            currency=payment_intent.currency,
            error="",
            raw_response=payment_intent.last_response,
            searchable_key=payment_intent.id,
        )

        create_transaction(
            payment,
            kind=kind,
            payment_information=None,  # type: ignore
            action_required=False,
            gateway_response=gateway_response,
        )

        manager = get_plugins_manager()
        discounts = fetch_active_discounts()
        lines = fetch_checkout_lines(payment.checkout)  # type: ignore
        checkout_info = fetch_checkout_info(
            payment.checkout, lines, discounts, manager  # type: ignore
        )
        order, _, _ = complete_checkout(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            payment_data={},
            store_source=False,
            discounts=discounts,
            user=payment.checkout.user or AnonymousUser(),  # type: ignore
        )
