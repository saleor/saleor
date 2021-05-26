from decimal import Decimal
from unittest.mock import patch

from stripe.error import AuthenticationError, StripeError
from stripe.stripe_object import StripeObject

from ..consts import METADATA_IDENTIFIER, WEBHOOK_EVENTS
from ..stripe_api import (
    create_payment_intent,
    delete_webhook,
    is_secret_api_key_valid,
    retrieve_payment_intent,
    subscribe_webhook,
)


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint",
)
def test_is_secret_api_key_valid_incorrect_key(mocked_webhook):
    api_key = "incorrect"
    mocked_webhook.list.side_effect = AuthenticationError()
    assert is_secret_api_key_valid(api_key) is False


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint",
)
def test_is_secret_api_key_valid_correct_key(mocked_webhook):
    api_key = "correct_key"
    assert is_secret_api_key_valid(api_key) is True

    mocked_webhook.list.assert_called_with(api_key)


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint",
)
def test_subscribe_webhook_returns_webhook_object(mocked_webhook):
    api_key = "api_key"
    expected_url = "http://mirumee.com/plugins/saleor.payments.stripe/webhooks/"

    subscribe_webhook(api_key)

    mocked_webhook.create.assert_called_with(
        api_key=api_key,
        url=expected_url,
        enabled_events=WEBHOOK_EVENTS,
        metadata={METADATA_IDENTIFIER: "mirumee.com"},
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint",
)
def test_delete_webhook(mocked_webhook):
    api_key = "api_key"

    delete_webhook(api_key, "webhook_id")

    mocked_webhook.delete.assert_called_with(
        "webhook_id",
        api_key=api_key,
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_create_payment_intent_returns_intent_object(mocked_payment_intent):
    api_key = "api_key"
    mocked_payment_intent.create.return_value = StripeObject()

    intent, error = create_payment_intent(api_key, Decimal(10), "USD")

    mocked_payment_intent.create.assert_called_with(
        api_key=api_key, amount="1000", currency="USD"
    )

    assert isinstance(intent, StripeObject)
    assert error is None


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_create_payment_intent_returns_error(mocked_payment_intent):
    api_key = "api_key"
    mocked_payment_intent.create.side_effect = StripeError(
        json_body={"error": "stripe-error"}
    )

    intent, error = create_payment_intent(api_key, Decimal(10), "USD")

    mocked_payment_intent.create.assert_called_with(
        api_key=api_key, amount="1000", currency="USD"
    )
    assert intent is None
    assert error


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_retrieve_payment_intent(mocked_payment_intent):
    api_key = "api_key"
    payment_intent_id = "id1234"

    mocked_payment_intent.retrieve.return_value = StripeObject()

    intent, _ = retrieve_payment_intent(api_key, payment_intent_id)

    mocked_payment_intent.retrieve.assert_called_with(
        payment_intent_id, api_key=api_key
    )
    assert isinstance(intent, StripeObject)


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_retrieve_payment_intent_stripe_returns_error(mocked_payment_intent):
    api_key = "api_key"
    payment_intent_id = "id1234"

    mocked_payment_intent.retrieve.side_effect = StripeError(
        json_body={"error": "stripe-error"}
    )

    _, error = retrieve_payment_intent(api_key, payment_intent_id)

    mocked_payment_intent.retrieve.assert_called_with(
        payment_intent_id, api_key=api_key
    )

    assert error == {"error": "stripe-error"}
