from decimal import Decimal
from math import isclose
from unittest.mock import Mock, patch

import pytest
import stripe
from django_countries import countries

from saleor.payment import ChargeStatus
from saleor.payment.gateways.stripe import (
    TransactionKind, _create_response, _get_client,
    _get_error_response_from_exc, _get_stripe_charge_payload, authorize,
    capture, charge, create_form, get_amount_for_stripe,
    get_amount_from_stripe, get_client_token, get_currency_for_stripe,
    get_currency_from_stripe, refund, void)
from saleor.payment.gateways.stripe.errors import (
    ORDER_NOT_AUTHORIZED, ORDER_NOT_CHARGED)
from saleor.payment.gateways.stripe.forms import (
    StripeCheckoutWidget, StripePaymentModalForm)
from saleor.payment.gateways.stripe.utils import (
    get_payment_billing_fullname, shipping_to_stripe_dict)
from saleor.payment.utils import create_payment_information

TRANSACTION_AMOUNT = Decimal(42.42)
TRANSACTION_REFUND_AMOUNT = Decimal(24.24)
TRANSACTION_CURRENCY = 'USD'
TRANSACTION_TOKEN = 'fake-stripe-id'
FAKE_TOKEN = 'fake-token'
ERROR_MESSAGE = 'error-message'


@pytest.fixture()
def gateway_params():
    return {
        'public_key': 'public',
        'secret_key': 'secret',
        'store_name': 'Saleor',
        'store_image': 'image.gif',
        'prefill': True,
        'remember_me': True,
        'locale': 'auto',
        'enable_billing_address': False,
        'enable_shipping_address': False}


@pytest.fixture()
def client_token():
    return FAKE_TOKEN


@pytest.fixture()
def stripe_payment(payment_dummy):
    payment_dummy.total = TRANSACTION_AMOUNT
    payment_dummy.currency = TRANSACTION_CURRENCY
    return payment_dummy


@pytest.fixture()
def stripe_authorized_payment(stripe_payment):
    stripe_payment.charge_status = ChargeStatus.NOT_CHARGED
    stripe_payment.save(update_fields=['charge_status'])

    return stripe_payment


@pytest.fixture()
def stripe_captured_payment(stripe_payment):
    stripe_payment.captured_amount = stripe_payment.total
    stripe_payment.charge_status = ChargeStatus.FULLY_CHARGED
    stripe_payment.save(update_fields=['captured_amount', 'charge_status'])

    return stripe_payment


@pytest.fixture()
def stripe_charged_payment(stripe_payment):
    stripe_payment.captured_amount = stripe_payment.total
    stripe_payment.charge_status = ChargeStatus.FULLY_CHARGED
    stripe_payment.save(update_fields=['captured_amount', 'charge_status'])

    stripe_payment.transactions.create(
        amount=stripe_payment.total,
        kind=TransactionKind.CHARGE,
        gateway_response={},
        is_success=True)
    return stripe_payment


@pytest.fixture()
def stripe_charge_success_response():
    return {
        'id': TRANSACTION_TOKEN,
        'amount': get_amount_for_stripe(
            TRANSACTION_AMOUNT, TRANSACTION_CURRENCY),
        'amount_refunded': 0,
        'currency': get_currency_for_stripe(TRANSACTION_CURRENCY),
        'status': 'succeeded'}


@pytest.fixture()
def stripe_partial_charge_success_response(stripe_charge_success_response):
    response = stripe_charge_success_response.copy()
    response['amount_refunded'] = get_amount_for_stripe(
        TRANSACTION_REFUND_AMOUNT, TRANSACTION_CURRENCY)
    return response


@pytest.fixture()
def stripe_refund_success_response(stripe_charge_success_response):
    response = stripe_charge_success_response.copy()
    response.pop('amount_refunded')
    response['amount'] = get_amount_for_stripe(
        TRANSACTION_REFUND_AMOUNT, TRANSACTION_CURRENCY)
    return response


def test_get_amount_for_stripe():
    assert get_amount_for_stripe(Decimal(1), 'USD') == 100
    assert get_amount_for_stripe(Decimal(1), 'usd') == 100

    assert get_amount_for_stripe(Decimal(0.01), 'USD') == 1
    assert get_amount_for_stripe(Decimal(24.24), 'USD') == 2424
    assert get_amount_for_stripe(Decimal(42.42), 'USD') == 4242

    assert get_amount_for_stripe(Decimal(1), 'JPY') == 1
    assert get_amount_for_stripe(Decimal(1), 'jpy') == 1


def test_get_amount_from_stripe():
    assert get_amount_from_stripe(100, 'USD') == Decimal(1)
    assert get_amount_from_stripe(100, 'usd') == Decimal(1)

    assert isclose(
        get_amount_from_stripe(1, 'USD'), Decimal(0.01))
    assert isclose(
        get_amount_from_stripe(2424, 'USD'), Decimal(24.24))
    assert isclose(
        get_amount_from_stripe(4242, 'USD'), Decimal(42.42))

    assert get_amount_from_stripe(1, 'JPY') == Decimal(1)
    assert get_amount_from_stripe(1, 'jpy') == Decimal(1)


def test_get_currency_for_stripe():
    assert get_currency_for_stripe('USD') == 'usd'
    assert get_currency_for_stripe('usd') == 'usd'
    assert get_currency_for_stripe('uSd') == 'usd'


def test_get_currency_from_stripe():
    assert get_currency_from_stripe('USD') == 'USD'
    assert get_currency_from_stripe('usd') == 'USD'
    assert get_currency_from_stripe('uSd') == 'USD'


def test_get_payment_billing_fullname(payment_dummy):
    payment_info = create_payment_information(payment_dummy)

    expected_fullname = '%s %s' % (
        payment_dummy.billing_last_name, payment_dummy.billing_first_name)
    assert get_payment_billing_fullname(payment_info) == expected_fullname


def test_shipping_address_to_stripe_dict(address):
    expected_address_dict = {
        'line1': address.street_address_1,
        'line2': address.street_address_2,
        'city': address.city,
        'state': address.country_area,
        'postal_code': address.postal_code,
        'country': dict(countries).get(address.country, '')}
    assert shipping_to_stripe_dict(address.as_data()) == expected_address_dict


def test_widget_with_default_options(stripe_payment, gateway_params):
    payment_info = create_payment_information(stripe_payment)
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert widget.render() == (
        '<script class="stripe-button" data-allow-remember-me="true" '
        'data-amount="4242" data-billing-address="false" data-currency="USD" '
        'data-description="Total payment" data-email="test@example.com" '
        'data-image="image.gif" data-key="public" data-locale="auto" '
        'data-name="Saleor" data-shipping-address="false" '
        'data-zip-code="false" src="https://checkout.stripe.com/checkout.js">'
        '</script>')


def test_widget_with_additional_attr(stripe_payment, gateway_params):
    payment_info = create_payment_information(stripe_payment)

    widget = StripeCheckoutWidget(
        payment_info, gateway_params, attrs={'data-custom': 'custom-data'})
    assert 'data-custom="custom-data"' in widget.render()


def test_widget_with_prefill_option(stripe_payment, gateway_params):
    payment_info = create_payment_information(stripe_payment)

    gateway_params['prefill'] = True
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert 'data-email="test@example.com"' in widget.render()

    gateway_params['prefill'] = False
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert 'data-email="test@example.com"' not in widget.render()


def test_widget_with_remember_me_option(stripe_payment, gateway_params):
    payment_info = create_payment_information(stripe_payment)

    gateway_params['remember_me'] = True
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert 'data-allow-remember-me="true"' in widget.render()

    gateway_params['remember_me'] = False
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert 'data-allow-remember-me="false"' in widget.render()


def test_widget_with_enable_billing_address_option(stripe_payment, gateway_params):
    payment_info = create_payment_information(stripe_payment, FAKE_TOKEN)

    gateway_params['enable_billing_address'] = True
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert 'data-billing-address="true"' in widget.render()
    assert 'data-zip-code="true"' in widget.render()

    gateway_params['enable_billing_address'] = False
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert 'data-billing-address="false"' in widget.render()
    assert 'data-zip-code="false"' in widget.render()


def test_widget_with_enable_shipping_address_option(stripe_payment, gateway_params):
    payment_info = create_payment_information(stripe_payment, FAKE_TOKEN)

    gateway_params['enable_shipping_address'] = True
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert 'data-shipping-address="true"' in widget.render()

    gateway_params['enable_shipping_address'] = False
    widget = StripeCheckoutWidget(payment_info, gateway_params)
    assert 'data-shipping-address="false"' in widget.render()


def test_stripe_payment_form(stripe_payment, gateway_params):
    payment_info = create_payment_information(stripe_payment, FAKE_TOKEN)
    form = create_form(
        None, payment_information=payment_info,
        connection_params=gateway_params)
    assert isinstance(form, StripePaymentModalForm)
    assert not form.is_valid()

    form = create_form(
        data={'stripeToken': FAKE_TOKEN}, payment_information=payment_info,
        connection_params=gateway_params)
    assert isinstance(form, StripePaymentModalForm)
    assert form.is_valid()


def test_get_client(gateway_params):
    assert _get_client(**gateway_params).api_key == 'secret'


def test_get_client_token():
    assert get_client_token() is None


def test_get_error_response_from_exc():
    stripe_error = stripe.error.StripeError(
        json_body={'message': ERROR_MESSAGE})
    invalid_request_error = stripe.error.InvalidRequestError(
        message=ERROR_MESSAGE, param=None)

    assert _get_error_response_from_exc(stripe_error) == {
        'message': ERROR_MESSAGE}
    assert _get_error_response_from_exc(invalid_request_error) == {}


def test_get_stripe_charge_payload_with_shipping(stripe_payment):
    payment_info = create_payment_information(stripe_payment, FAKE_TOKEN)
    billing_name = get_payment_billing_fullname(payment_info)
    expected_payload = {
        'capture': True,
        'amount': get_amount_for_stripe(
            TRANSACTION_AMOUNT, TRANSACTION_CURRENCY),
        'currency': get_currency_for_stripe(TRANSACTION_CURRENCY),
        'source': FAKE_TOKEN,
        'description': billing_name,
        'shipping': {
            'name': billing_name,
            'address': shipping_to_stripe_dict(payment_info['shipping'])}}

    charge_payload = _get_stripe_charge_payload(payment_info, True)

    assert charge_payload == expected_payload


def test_get_stripe_charge_payload_without_shipping(stripe_payment):
    stripe_payment.order.shipping_address = None
    payment_info = create_payment_information(stripe_payment, FAKE_TOKEN)
    billing_name = get_payment_billing_fullname(payment_info)
    expected_payload = {
        'capture': True,
        'amount': get_amount_for_stripe(
            TRANSACTION_AMOUNT, TRANSACTION_CURRENCY),
        'currency': get_currency_for_stripe(TRANSACTION_CURRENCY),
        'source': FAKE_TOKEN,
        'description': billing_name}

    charge_payload = _get_stripe_charge_payload(payment_info, True)

    assert charge_payload == expected_payload


def test_create_transaction_with_charge_success_response(
        stripe_payment,
        stripe_charge_success_response):
    payment_info = create_payment_information(stripe_payment)

    response = _create_response(
        payment_information=payment_info, kind='ANYKIND',
        response=stripe_charge_success_response, error=None)

    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['is_success'] is True
    assert isclose(response['amount'], TRANSACTION_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY


def test_create_transaction_with_partial_charge_success_response(
        stripe_payment,
        stripe_partial_charge_success_response):
    payment_info = create_payment_information(stripe_payment)

    response = _create_response(
        payment_information=payment_info, kind='ANYKIND',
        response=stripe_partial_charge_success_response, error=None)

    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['is_success'] is True
    assert isclose(
        response['amount'], TRANSACTION_AMOUNT - TRANSACTION_REFUND_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY


def test_create_transaction_with_refund_success_response(
        stripe_payment,
        stripe_refund_success_response):
    payment_info = create_payment_information(stripe_payment)

    response = _create_response(
        payment_information=payment_info, kind='ANYKIND',
        response=stripe_refund_success_response, error=None)

    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['is_success'] is True
    assert isclose(response['amount'], TRANSACTION_REFUND_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY


def test_create_response_with_error_response(stripe_payment):
    payment = stripe_payment
    payment_info = create_payment_information(payment, FAKE_TOKEN)
    stripe_error_response = {}

    response = _create_response(
        payment_information=payment_info, kind='ANYKIND',
        response=stripe_error_response, error=None)

    assert response['transaction_id'] == FAKE_TOKEN
    assert response['is_success'] is False
    assert response['amount'] == payment.total
    assert response['currency'] == payment.currency


@pytest.mark.integration
@patch('stripe.Charge.create')
def test_authorize(
        mock_charge_create,
        stripe_payment,
        gateway_params,
        stripe_charge_success_response):
    payment = stripe_payment
    payment_info = create_payment_information(payment, FAKE_TOKEN)
    response = stripe_charge_success_response
    mock_charge_create.return_value = response

    response = authorize(payment_info, gateway_params)

    assert not response['error']
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.AUTH
    assert response['is_success']
    assert isclose(response['amount'], TRANSACTION_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == stripe_charge_success_response


@pytest.mark.integration
@patch('stripe.Charge.create')
def test_authorize_error_response(
        mock_charge_create,
        stripe_payment,
        gateway_params):
    payment = stripe_payment
    payment_info = create_payment_information(payment, FAKE_TOKEN)
    stripe_error = stripe.error.InvalidRequestError(
        message=ERROR_MESSAGE, param=None)
    mock_charge_create.side_effect = stripe_error

    response = authorize(payment_info, gateway_params)

    assert response['error'] == ERROR_MESSAGE
    assert response['transaction_id'] == FAKE_TOKEN
    assert response['kind'] == TransactionKind.AUTH
    assert not response['is_success']
    assert response['amount'] == payment.total
    assert response['currency'] == payment.currency
    assert response['raw_response'] == _get_error_response_from_exc(
        stripe_error)


@pytest.mark.integration
@patch('stripe.Charge.retrieve')
def test_capture(
        mock_charge_retrieve,
        stripe_authorized_payment,
        gateway_params,
        stripe_charge_success_response):
    payment = stripe_authorized_payment
    payment_info = create_payment_information(
        payment, amount=TRANSACTION_AMOUNT)
    response = stripe_charge_success_response
    mock_charge_retrieve.return_value = Mock(
        capture=Mock(return_value=response))

    response = capture(payment_info, gateway_params)

    assert not response['error']
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.CAPTURE
    assert response['is_success']
    assert isclose(response['amount'], TRANSACTION_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == stripe_charge_success_response


@pytest.mark.integration
@patch('stripe.Charge.retrieve')
def test_partial_capture(
        mock_charge_retrieve,
        stripe_authorized_payment,
        gateway_params,
        stripe_partial_charge_success_response):
    payment = stripe_authorized_payment
    payment_info = create_payment_information(
        payment, amount=TRANSACTION_AMOUNT)
    response = stripe_partial_charge_success_response
    mock_charge_retrieve.return_value = Mock(
        capture=Mock(return_value=response))

    response = capture(payment_info, gateway_params)

    assert not response['error']
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.CAPTURE
    assert response['is_success']
    assert isclose(response['amount'], TRANSACTION_AMOUNT - TRANSACTION_REFUND_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == stripe_partial_charge_success_response


@pytest.mark.integration
@patch('stripe.Charge.retrieve')
def test_capture_error_response(
        mock_charge_retrieve,
        stripe_authorized_payment,
        gateway_params):
    payment = stripe_authorized_payment
    payment_info = create_payment_information(
        payment, TRANSACTION_TOKEN, amount=TRANSACTION_AMOUNT)
    stripe_error = stripe.error.InvalidRequestError(
        message=ERROR_MESSAGE, param=None)
    mock_charge_retrieve.side_effect = stripe_error

    response = capture(payment_info, gateway_params)

    assert response['error'] == ERROR_MESSAGE
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.CAPTURE
    assert not response['is_success']
    assert response['amount'] == payment.total
    assert response['currency'] == payment.currency
    assert response['raw_response'] == _get_error_response_from_exc(
        stripe_error)


@pytest.mark.integration
@patch('stripe.Charge.create')
def test_charge(
        mock_charge_create,
        stripe_payment,
        gateway_params,
        stripe_charge_success_response):
    payment = stripe_payment
    payment_info = create_payment_information(
        payment, FAKE_TOKEN, TRANSACTION_AMOUNT)
    response = stripe_charge_success_response
    mock_charge_create.return_value = response

    response = charge(payment_info, gateway_params)

    assert not response['error']
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.CHARGE
    assert response['is_success']
    assert isclose(response['amount'], TRANSACTION_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == stripe_charge_success_response


@pytest.mark.integration
@patch('stripe.Charge.create')
def test_charge_error_response(
        mock_charge_create,
        stripe_payment,
        gateway_params):
    payment = stripe_payment
    payment_info = create_payment_information(
        payment, FAKE_TOKEN, TRANSACTION_AMOUNT)
    stripe_error = stripe.error.InvalidRequestError(
        message=ERROR_MESSAGE, param=None)
    mock_charge_create.side_effect = stripe_error

    response = charge(payment_info, gateway_params)

    assert response['error'] == ERROR_MESSAGE
    assert response['transaction_id'] == FAKE_TOKEN
    assert response['kind'] == TransactionKind.CHARGE
    assert not response['is_success']
    assert response['amount'] == payment.total
    assert response['currency'] == payment.currency
    assert response['raw_response'] == _get_error_response_from_exc(
        stripe_error)


@pytest.mark.integration
@patch('stripe.Refund.create')
@patch('stripe.Charge.retrieve')
def test_refund_charged(
        mock_charge_retrieve,
        mock_refund_create,
        stripe_charged_payment,
        gateway_params,
        stripe_refund_success_response):
    payment = stripe_charged_payment
    payment_info = create_payment_information(
        payment, TRANSACTION_TOKEN, amount=TRANSACTION_AMOUNT)
    response = stripe_refund_success_response
    mock_charge_retrieve.return_value = Mock(id='')
    mock_refund_create.return_value = response

    response = refund(payment_info, gateway_params)

    assert not response['error']
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.REFUND
    assert response['is_success']
    assert isclose(response['amount'], TRANSACTION_REFUND_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == stripe_refund_success_response


@pytest.mark.integration
@patch('stripe.Refund.create')
@patch('stripe.Charge.retrieve')
def test_refund_captured(
        mock_charge_retrieve,
        mock_refund_create,
        stripe_captured_payment,
        gateway_params,
        stripe_refund_success_response):
    payment = stripe_captured_payment
    payment_info = create_payment_information(
        payment, amount=TRANSACTION_AMOUNT)
    response = stripe_refund_success_response
    mock_charge_retrieve.return_value = Mock(id='')
    mock_refund_create.return_value = response

    response = refund(payment_info, gateway_params)

    assert not response['error']
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.REFUND
    assert response['is_success']
    assert isclose(response['amount'], TRANSACTION_REFUND_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == stripe_refund_success_response


@pytest.mark.integration
@patch('stripe.Refund.create')
@patch('stripe.Charge.retrieve')
def test_refund_error_response(
        mock_charge_retrieve,
        mock_refund_create,
        stripe_charged_payment,
        gateway_params):
    payment = stripe_charged_payment
    payment_info = create_payment_information(
        payment, TRANSACTION_TOKEN, amount=TRANSACTION_AMOUNT)
    mock_charge_retrieve.return_value = Mock(id='')
    stripe_error = stripe.error.InvalidRequestError(
        message=ERROR_MESSAGE, param=None)
    mock_refund_create.side_effect = stripe_error

    response = refund(payment_info, gateway_params)

    assert response['error'] == ERROR_MESSAGE
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.REFUND
    assert not response['is_success']
    assert response['amount'] == payment.total
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == _get_error_response_from_exc(
        stripe_error)


@pytest.mark.integration
@patch('stripe.Refund.create')
@patch('stripe.Charge.retrieve')
def test_void(
        mock_charge_retrieve,
        mock_refund_create,
        stripe_authorized_payment,
        gateway_params,
        stripe_refund_success_response):
    payment = stripe_authorized_payment
    payment_info = create_payment_information(payment, TRANSACTION_TOKEN)
    response = stripe_refund_success_response
    mock_charge_retrieve.return_value = Mock(id='')
    mock_refund_create.return_value = response

    response = void(payment_info, gateway_params)

    assert not response['error']
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.VOID
    assert response['is_success']
    assert isclose(response['amount'], TRANSACTION_REFUND_AMOUNT)
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == stripe_refund_success_response


@pytest.mark.integration
@patch('stripe.Refund.create')
@patch('stripe.Charge.retrieve')
def test_void_error_response(
        mock_charge_retrieve,
        mock_refund_create,
        stripe_authorized_payment,
        gateway_params):
    payment = stripe_authorized_payment
    payment_info = create_payment_information(payment, TRANSACTION_TOKEN)
    mock_charge_retrieve.return_value = Mock(id='')
    stripe_error = stripe.error.InvalidRequestError(
        message=ERROR_MESSAGE, param=None)
    mock_refund_create.side_effect = stripe_error

    response = void(payment_info, gateway_params)

    assert response['error'] == ERROR_MESSAGE
    assert response['transaction_id'] == TRANSACTION_TOKEN
    assert response['kind'] == TransactionKind.VOID
    assert not response['is_success']
    assert response['amount'] == payment.total
    assert response['currency'] == TRANSACTION_CURRENCY
    assert response['raw_response'] == {}
