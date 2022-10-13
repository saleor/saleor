from unittest.mock import Mock, patch

from .... import TransactionKind
from ....utils import create_payment_information, price_to_minor_unit
from ..consts import AUTOMATIC_CAPTURE_METHOD, STRIPE_API_VERSION, SUCCESS_STATUS


@patch("saleor.payment.gateways.stripe.stripe_api.stripe.Customer.create")
@patch("saleor.payment.gateways.stripe.stripe_api.stripe.PaymentIntent.create")
def test_process_payment_with_customer_and_future_usage(
    mocked_payment_intent,
    mocked_customer_create,
    stripe_plugin,
    payment_stripe_for_checkout,
    channel_USD,
    customer_user,
):
    customer = Mock()
    mocked_customer_create.return_value = customer

    payment_intent = Mock()
    mocked_payment_intent.return_value = payment_intent

    client_secret = "client-secret"
    dummy_response = {
        "id": "evt_1Ip9ANH1Vac4G4dbE9ch7zGS",
    }
    dummy_charges = {}
    payment_intent_id = "payment-intent-id"
    payment_intent.id = payment_intent_id
    payment_intent.client_secret = client_secret
    payment_intent.last_response.data = dummy_response
    payment_intent.status = SUCCESS_STATUS
    payment_intent.get.side_effect = dummy_charges.get

    plugin = stripe_plugin(auto_capture=True)

    payment_stripe_for_checkout.checkout.user = customer_user
    payment_stripe_for_checkout.checkout.email = customer_user.email
    payment_info = create_payment_information(
        payment_stripe_for_checkout,
        customer_id=None,
        store_source=True,
        additional_data={"setup_future_usage": "off_session"},
    )

    response = plugin.process_payment(payment_info, None)

    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.CAPTURE
    assert response.amount == payment_info.amount
    assert response.currency == payment_info.currency
    assert response.transaction_id == payment_intent_id
    assert response.error is None
    assert response.raw_response == dummy_response
    assert response.action_required_data == {
        "client_secret": client_secret,
        "id": payment_intent_id,
    }

    api_key = plugin.config.connection_params["secret_api_key"]
    mocked_payment_intent.assert_called_once_with(
        api_key=api_key,
        amount=price_to_minor_unit(payment_info.amount, payment_info.currency),
        currency=payment_info.currency,
        capture_method=AUTOMATIC_CAPTURE_METHOD,
        customer=customer,
        setup_future_usage="off_session",
        metadata={
            "channel": channel_USD.slug,
            "payment_id": payment_info.graphql_payment_id,
        },
        receipt_email=payment_stripe_for_checkout.checkout.email,
        stripe_version=STRIPE_API_VERSION,
    )

    mocked_customer_create.assert_called_once_with(
        api_key="secret_key",
        email=customer_user.email,
        stripe_version=STRIPE_API_VERSION,
    )
