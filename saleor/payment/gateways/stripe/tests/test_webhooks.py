from unittest.mock import patch

import pytest
from stripe.stripe_object import StripeObject

from .....checkout.complete_checkout import complete_checkout
from .... import TransactionKind
from ....utils import price_to_minor_unit
from ..webhooks import handle_successful_payment_intent


@pytest.mark.parametrize(
    "kind, method",
    [(TransactionKind.AUTH, "manual"), (TransactionKind.CAPTURE, "automatic")],
)
@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
def test_handle_successful_payment_intent_for_checkout(
    wrapped_checkout_complete,
    kind,
    method,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
):
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    payment_intent["currency"] = payment.currency
    payment_intent["capture_method"] = method
    handle_successful_payment_intent(payment_intent, plugin.config)

    payment.refresh_from_db()

    assert wrapped_checkout_complete.called
    assert payment.checkout_id is None
    assert payment.order
    assert payment.order.checkout_token == str(checkout_with_items.token)
    transaction = payment.transactions.get(kind=kind)
    assert transaction.token == payment_intent.id


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
def test_handle_successful_payment_intent_for_order(
    wrapped_checkout_complete,
    payment_stripe_for_order,
    checkout_with_items,
    stripe_plugin,
):

    payment = payment_stripe_for_order
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["capture_method"] = "automatic"
    handle_successful_payment_intent(payment_intent, plugin.config)

    payment.refresh_from_db()

    assert wrapped_checkout_complete.called is False
