from decimal import Decimal
from unittest.mock import patch

from stripe.error import AuthenticationError, StripeError
from stripe.stripe_object import StripeObject

from saleor.payment.utils import price_to_minor_unit

from ..consts import (
    AUTOMATIC_CAPTURE_METHOD,
    MANUAL_CAPTURE_METHOD,
    METADATA_IDENTIFIER,
    WEBHOOK_EVENTS,
)
from ..stripe_api import (
    cancel_payment_intent,
    capture_payment_intent,
    create_payment_intent,
    delete_webhook,
    is_secret_api_key_valid,
    refund_payment_intent,
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

    intent, error = create_payment_intent(
        api_key, Decimal(10), "USD", auto_capture=True
    )

    mocked_payment_intent.create.assert_called_with(
        api_key=api_key,
        amount="1000",
        currency="USD",
        capture_method=AUTOMATIC_CAPTURE_METHOD,
    )

    assert isinstance(intent, StripeObject)
    assert error is None


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_create_payment_intent_manual_auto_capture(mocked_payment_intent):
    api_key = "api_key"
    mocked_payment_intent.create.return_value = StripeObject()

    intent, error = create_payment_intent(
        api_key, Decimal(10), "USD", auto_capture=False
    )

    mocked_payment_intent.create.assert_called_with(
        api_key=api_key,
        amount="1000",
        currency="USD",
        capture_method=MANUAL_CAPTURE_METHOD,
    )


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
        api_key=api_key,
        amount="1000",
        currency="USD",
        capture_method=AUTOMATIC_CAPTURE_METHOD,
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

    expected_error = StripeError(message="stripe-error")
    mocked_payment_intent.retrieve.side_effect = expected_error

    _, error = retrieve_payment_intent(api_key, payment_intent_id)

    mocked_payment_intent.retrieve.assert_called_with(
        payment_intent_id, api_key=api_key
    )

    assert error == expected_error


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_capture_payment_intent(mocked_payment_intent):
    api_key = "api_key"
    payment_intent_id = "id1234"
    amount = price_to_minor_unit(Decimal("10.0"), "USD")

    mocked_payment_intent.capture.return_value = StripeObject()

    intent, _ = capture_payment_intent(
        api_key=api_key, payment_intent_id=payment_intent_id, amount_to_capture=amount
    )

    mocked_payment_intent.capture.assert_called_with(
        payment_intent_id, amount_to_capture=amount, api_key=api_key
    )
    assert isinstance(intent, StripeObject)


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_capture_payment_intent_stripe_returns_error(mocked_payment_intent):
    api_key = "api_key"
    payment_intent_id = "id1234"
    amount = price_to_minor_unit(Decimal("10.0"), "USD")

    expected_error = StripeError(message="stripe-error")
    mocked_payment_intent.capture.side_effect = expected_error

    _, error = capture_payment_intent(
        api_key=api_key, payment_intent_id=payment_intent_id, amount_to_capture=amount
    )

    mocked_payment_intent.capture.assert_called_with(
        payment_intent_id, amount_to_capture=amount, api_key=api_key
    )

    assert error == expected_error


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.Refund",
)
def test_refund_payment_intent(mocked_refund):
    api_key = "api_key"
    payment_intent_id = "id1234"
    amount = price_to_minor_unit(Decimal("10.0"), "USD")

    mocked_refund.create.return_value = StripeObject()

    intent, _ = refund_payment_intent(
        api_key=api_key, payment_intent_id=payment_intent_id, amount_to_refund=amount
    )

    mocked_refund.create.assert_called_with(
        payment_intent=payment_intent_id, amount=amount, api_key=api_key
    )
    assert isinstance(intent, StripeObject)


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.Refund",
)
def test_refund_payment_intent_returns_error(mocked_refund):
    api_key = "api_key"
    payment_intent_id = "id1234"
    amount = price_to_minor_unit(Decimal("10.0"), "USD")

    expected_error = StripeError(message="stripe-error")
    mocked_refund.create.side_effect = expected_error

    _, error = refund_payment_intent(
        api_key=api_key, payment_intent_id=payment_intent_id, amount_to_refund=amount
    )

    mocked_refund.create.assert_called_with(
        payment_intent=payment_intent_id, amount=amount, api_key=api_key
    )
    assert error == expected_error


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_cancel_payment_intent(mocked_payment_intent):
    api_key = "api_key"
    payment_intent_id = "id1234"

    mocked_payment_intent.cancel.return_value = StripeObject()

    intent, _ = cancel_payment_intent(
        api_key=api_key, payment_intent_id=payment_intent_id
    )

    mocked_payment_intent.cancel.assert_called_with(payment_intent_id, api_key=api_key)
    assert isinstance(intent, StripeObject)


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_cancel_payment_intent_stripe_returns_error(mocked_payment_intent):
    api_key = "api_key"
    payment_intent_id = "id1234"

    expected_error = StripeError(message="stripe-error")
    mocked_payment_intent.cancel.side_effect = expected_error

    _, error = cancel_payment_intent(
        api_key=api_key, payment_intent_id=payment_intent_id
    )

    mocked_payment_intent.cancel.assert_called_with(payment_intent_id, api_key=api_key)

    assert error == expected_error
