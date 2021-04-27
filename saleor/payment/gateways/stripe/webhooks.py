import logging

import stripe
from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from stripe.error import SignatureVerificationError
from stripe.stripe_object import StripeObject

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse
from ...models import Payment
from ...utils import price_from_minor_unit, create_transaction
from ....checkout.complete_checkout import complete_checkout
from ....checkout.fetch import fetch_checkout_lines, fetch_checkout_info
from ....checkout.models import Checkout
from ....core.transactions import transaction_with_commit_on_errors
from ....discount.utils import fetch_active_discounts
from ....plugins.manager import get_plugins_manager

logger = logging.getLogger(__name__)


@transaction_with_commit_on_errors()
def handle_webhook(request: WSGIRequest, gateway_config: "GatewayConfig"):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = gateway_config.connection_params["webhook_secret"]
    api_key = gateway_config.connection_params["secret_api_key"]
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret, api_key=api_key
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        handle_successful_payment_intent(payment_intent, gateway_config)
    # elif event.type == 'payment_method.attached':
    #     payment_method = event.data.object  # contains a stripe.PaymentMethod
    #     print('PaymentMethod was attached to a Customer!')
    # # ... handle other event types
    # else:
    #     print('Unhandled event type {}'.format(event.type))

    return HttpResponse(status=200)


def handle_successful_payment_intent(payment_intent: StripeObject, gateway_config:"GatewayConfig"):
    checkout = Checkout.objects.prefetch_related("payments").select_for_update(of=("self", )).filter(payments__transactions__token=payment_intent.id, payments__is_active=True).first()
    if checkout:
        payment = checkout.payments.first()
    else:
        payment = (
            Payment.objects.prefetch_related("checkout")
            .select_for_update(of=("self", ))
            .filter(transactions__token=payment_intent.id, is_active=True).first())
    if not payment:
        logger.warning(
            "Payment for PaymentIntent %s was not found",
            payment_intent.id,
        )
        return
    if payment.order_id:
        # Order already created
        return

    if payment.checkout:
        # If the payment is not Auth/Capture, it means that user didn't return to the
        # storefront and we need to finalize the checkout asynchronously.

        gateway_response = GatewayResponse(
            kind=TransactionKind.ACTION_TO_CONFIRM,
            action_required=False,
            transaction_id=payment_intent.id,
            is_success=True,
            amount=price_from_minor_unit(payment_intent.amount, payment_intent.currency),
            currency=payment_intent.currency,
            error="",
            raw_response=payment_intent.last_response,
            searchable_key=payment_intent.id,
        )

        create_transaction(
            payment,
            kind=TransactionKind.ACTION_TO_CONFIRM,
            payment_information=None,
            action_required=False,
            gateway_response=gateway_response,
        )

        manager = get_plugins_manager()
        discounts = fetch_active_discounts()
        lines = fetch_checkout_lines(payment.checkout)
        checkout_info = fetch_checkout_info(payment.checkout, lines, discounts, manager)
        order, _, _ = complete_checkout(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            payment_data={},
            store_source=False,
            discounts=discounts,
            user=payment.checkout.user or AnonymousUser(),
        )

