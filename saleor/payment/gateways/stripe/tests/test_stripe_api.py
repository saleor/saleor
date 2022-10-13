from decimal import Decimal
from unittest.mock import patch

from stripe.error import AuthenticationError, StripeError
from stripe.stripe_object import StripeObject

from saleor.payment.interface import PaymentMethodInfo
from saleor.payment.utils import price_to_minor_unit

from ..consts import (
    AUTOMATIC_CAPTURE_METHOD,
    MANUAL_CAPTURE_METHOD,
    METADATA_IDENTIFIER,
    STRIPE_API_VERSION,
    WEBHOOK_EVENTS,
)
from ..stripe_api import (
    cancel_payment_intent,
    capture_payment_intent,
    create_payment_intent,
    delete_webhook,
    get_or_create_customer,
    get_payment_method_details,
    is_secret_api_key_valid,
    list_customer_payment_methods,
    refund_payment_intent,
    retrieve_payment_intent,
    subscribe_webhook,
    update_payment_method,
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

    mocked_webhook.list.assert_called_with(api_key, stripe_version=STRIPE_API_VERSION)


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint",
)
def test_subscribe_webhook_returns_webhook_object(mocked_webhook, channel_USD):
    api_key = "api_key"
    expected_url = (
        "http://mirumee.com/plugins/channel/main/saleor.payments.stripe/webhooks/"
    )

    subscribe_webhook(api_key, channel_slug=channel_USD.slug)

    mocked_webhook.create.assert_called_with(
        api_key=api_key,
        url=expected_url,
        enabled_events=WEBHOOK_EVENTS,
        metadata={METADATA_IDENTIFIER: "mirumee.com"},
        stripe_version=STRIPE_API_VERSION,
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint",
)
def test_delete_webhook(mocked_webhook):
    api_key = "api_key"

    delete_webhook(api_key, "webhook_id")

    mocked_webhook.delete.assert_called_with(
        "webhook_id", api_key=api_key, stripe_version=STRIPE_API_VERSION
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
        stripe_version=STRIPE_API_VERSION,
    )

    assert isinstance(intent, StripeObject)
    assert error is None


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_create_payment_intent_with_customer(mocked_payment_intent):
    customer = StripeObject(id="c_ABC")
    api_key = "api_key"
    mocked_payment_intent.create.return_value = StripeObject()

    intent, error = create_payment_intent(
        api_key, Decimal(10), "USD", auto_capture=True, customer=customer
    )

    mocked_payment_intent.create.assert_called_with(
        api_key=api_key,
        amount="1000",
        currency="USD",
        capture_method=AUTOMATIC_CAPTURE_METHOD,
        customer=customer,
        stripe_version=STRIPE_API_VERSION,
    )

    assert isinstance(intent, StripeObject)
    assert error is None


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_create_payment_intent_manual_auto_capture(mocked_payment_intent):
    api_key = "api_key"
    mocked_payment_intent.create.return_value = StripeObject()

    _intent, _error = create_payment_intent(
        api_key, Decimal(10), "USD", auto_capture=False
    )

    mocked_payment_intent.create.assert_called_with(
        api_key=api_key,
        amount="1000",
        currency="USD",
        capture_method=MANUAL_CAPTURE_METHOD,
        stripe_version=STRIPE_API_VERSION,
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
        stripe_version=STRIPE_API_VERSION,
    )
    assert intent is None
    assert error


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentMethod",
)
def test_update_payment_method(mocked_payment_method):
    # given
    api_key = "api_key"
    payment_method_id = "1234"
    metadata = {"key": "value"}

    # when
    update_payment_method(api_key, payment_method_id, metadata)

    # then
    mocked_payment_method.modify.assert_called_once_with(
        payment_method_id,
        api_key=api_key,
        metadata=metadata,
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent",
)
def test_retrieve_payment_intent(mocked_payment_intent):
    api_key = "api_key"
    payment_intent_id = "id1234"

    mocked_payment_intent.retrieve.return_value = StripeObject()

    intent, _ = retrieve_payment_intent(api_key, payment_intent_id)

    mocked_payment_intent.retrieve.assert_called_with(
        payment_intent_id,
        api_key=api_key,
        stripe_version=STRIPE_API_VERSION,
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
        payment_intent_id,
        api_key=api_key,
        stripe_version=STRIPE_API_VERSION,
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
        payment_intent_id,
        amount_to_capture=amount,
        api_key=api_key,
        stripe_version=STRIPE_API_VERSION,
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
        payment_intent_id,
        amount_to_capture=amount,
        api_key=api_key,
        stripe_version=STRIPE_API_VERSION,
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
        payment_intent=payment_intent_id,
        amount=amount,
        api_key=api_key,
        stripe_version=STRIPE_API_VERSION,
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
        payment_intent=payment_intent_id,
        amount=amount,
        api_key=api_key,
        stripe_version=STRIPE_API_VERSION,
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

    mocked_payment_intent.cancel.assert_called_with(
        payment_intent_id, api_key=api_key, stripe_version=STRIPE_API_VERSION
    )
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

    mocked_payment_intent.cancel.assert_called_with(
        payment_intent_id, api_key=api_key, stripe_version=STRIPE_API_VERSION
    )

    assert error == expected_error


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.Customer",
)
def test_get_or_create_customer_retrieve(mocked_customer):
    mocked_customer.retrieve.return_value = StripeObject()
    api_key = "123"
    customer_email = "admin@example.com"
    customer_id = "c_12345"

    customer = get_or_create_customer(
        api_key=api_key,
        customer_email=customer_email,
        customer_id=customer_id,
    )

    assert isinstance(customer, StripeObject)
    mocked_customer.retrieve.assert_called_with(
        customer_id, api_key=api_key, stripe_version=STRIPE_API_VERSION
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.Customer",
)
def test_get_or_create_customer_failed_retrieve(mocked_customer):

    expected_error = StripeError(message="stripe-error")
    mocked_customer.retrieve.side_effect = expected_error

    api_key = "123"
    customer_email = "admin@example.com"
    customer_id = "c_12345"

    customer = get_or_create_customer(
        api_key=api_key,
        customer_email=customer_email,
        customer_id=customer_id,
    )

    assert customer is None
    mocked_customer.retrieve.assert_called_with(
        customer_id, api_key=api_key, stripe_version=STRIPE_API_VERSION
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.Customer",
)
def test_get_or_create_customer_create(mocked_customer):
    mocked_customer.create.return_value = StripeObject()
    api_key = "123"
    customer_email = "admin@example.com"
    customer = get_or_create_customer(
        api_key=api_key,
        customer_email=customer_email,
        customer_id=None,
    )

    assert isinstance(customer, StripeObject)
    mocked_customer.create.assert_called_with(
        email=customer_email, api_key=api_key, stripe_version=STRIPE_API_VERSION
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.Customer",
)
def test_get_or_create_customer_failed_create(mocked_customer):
    expected_error = StripeError(message="stripe-error")
    mocked_customer.create.side_effect = expected_error

    api_key = "123"
    customer_email = "admin@example.com"
    customer = get_or_create_customer(
        api_key=api_key,
        customer_email=customer_email,
        customer_id=None,
    )

    assert customer is None
    mocked_customer.create.assert_called_with(
        email=customer_email, api_key=api_key, stripe_version=STRIPE_API_VERSION
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentMethod",
)
def test_list_customer_payment_methods(mocked_payment_method):
    api_key = "123"
    customer_id = "c_customer_id"
    mocked_payment_method.list.return_value = StripeObject()

    payment_method, error = list_customer_payment_methods(
        api_key=api_key, customer_id=customer_id
    )

    assert error is None
    assert isinstance(payment_method, StripeObject)
    mocked_payment_method.list.assert_called_with(
        api_key=api_key,
        customer=customer_id,
        type="card",
        stripe_version=STRIPE_API_VERSION,
    )


@patch(
    "saleor.payment.gateways.stripe.stripe_api.stripe.PaymentMethod",
)
def test_list_customer_payment_methods_failed_to_fetch(mocked_payment_method):
    api_key = "123"
    customer_id = "c_customer_id"

    expected_error = StripeError(message="stripe-error")
    mocked_payment_method.list.side_effect = expected_error

    payment_method, error = list_customer_payment_methods(
        api_key=api_key, customer_id=customer_id
    )

    assert payment_method is None
    assert isinstance(error, StripeError)

    mocked_payment_method.list.assert_called_with(
        api_key=api_key,
        customer=customer_id,
        type="card",
        stripe_version=STRIPE_API_VERSION,
    )


def test_get_payment_method_details():
    payment_intent = StripeObject()
    payment_intent.charges = {
        "data": [
            {
                "payment_method_details": {
                    "type": "card",
                    "card": {
                        "last4": "1234",
                        "exp_year": "2222",
                        "exp_month": "12",
                        "brand": "visa",
                    },
                }
            }
        ]
    }

    payment_method_info = get_payment_method_details(payment_intent)

    assert payment_method_info == PaymentMethodInfo(
        last_4="1234",
        exp_year=2222,
        exp_month=12,
        brand="visa",
        type="card",
    )


def test_get_payment_method_details_missing_charges():
    payment_intent = StripeObject()
    payment_intent.charges = None

    payment_method_info = get_payment_method_details(payment_intent)

    assert payment_method_info is None


def test_get_payment_method_details_missing_charges_data():
    payment_intent = StripeObject()
    payment_intent.charges = {"data": None}

    payment_method_info = get_payment_method_details(payment_intent)

    assert payment_method_info is None
