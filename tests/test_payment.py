from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from prices import Money

from saleor.order import OrderEvents, OrderEventsEmails
from saleor.payment import (
    ChargeStatus, PaymentError, Transactions, get_payment_gateway)
from saleor.payment.utils import (
    create_payment, create_transaction, gateway_authorize, gateway_capture,
    gateway_get_client_token, gateway_refund, gateway_void,
    get_billing_data, handle_fully_paid_order, validate_payment)

NOT_ACTIVE_PAYMENT_ERROR = 'This payment is no longer active.'
EXAMPLE_ERROR = 'Example dummy error'


@pytest.fixture
def transaction_data(payment_dummy, settings):
    return {
        'payment': payment_dummy,
        'token': 'token',
        'kind': Transactions.CAPTURE,
        'is_success': True,
        'amount': Decimal('10.00'),
        'currency': settings.DEFAULT_CURRENCY,
        'gateway_response': {
            'credit_cart': '4321'}}


@pytest.fixture
def gateway_params():
    return {'secret-key': 'nobodylikesspanishinqusition'}


@pytest.fixture
def transaction_token():
    return 'transaction-token'


def test_get_billing_data(order):
    assert order.billing_address
    result = get_billing_data(order)
    expected_result = {
        'billing_first_name': order.billing_address.first_name,
        'billing_last_name': order.billing_address.last_name,
        'billing_company_name': order.billing_address.company_name,
        'billing_address_1': order.billing_address.street_address_1,
        'billing_address_2': order.billing_address.street_address_2,
        'billing_city': order.billing_address.city,
        'billing_postal_code': order.billing_address.postal_code,
        'billing_country_code': order.billing_address.country.code,
        'billing_email': order.user_email,
        'billing_country_area': order.billing_address.country_area}
    assert result == expected_result

    order.billing_address = None
    assert get_billing_data(order) == {}


def test_get_payment_gateway_not_allowed_checkout_choice(settings):
    gateway = 'example-gateway'
    settings.CHECKOUT_PAYMENT_GATEWAYS = {}
    with pytest.raises(ValueError):
        get_payment_gateway(gateway)


def test_get_payment_gateway_non_existing_name(settings):
    gateway = 'example-gateway'
    settings.CHECKOUT_PAYMENT_GATEWAYS = {gateway: 'Example gateway'}
    with pytest.raises(ImproperlyConfigured):
        get_payment_gateway(gateway)


def test_get_payment_gateway(settings):
    gateway_name = list(settings.PAYMENT_GATEWAYS.keys())[0]
    gateway = settings.PAYMENT_GATEWAYS[gateway_name]
    gateway_module, gateway_params = get_payment_gateway(gateway_name)
    assert gateway_module.__name__ == gateway['module']
    assert gateway_params == gateway['connection_params']


@patch('saleor.order.emails.send_payment_confirmation.delay')
def test_handle_fully_paid_order_no_email(
        mock_send_payment_confirmation, order):
    order.user = None
    order.user_email = ''

    handle_fully_paid_order(order)
    event = order.events.get()
    assert event.type == OrderEvents.ORDER_FULLY_PAID.value
    assert not mock_send_payment_confirmation.called


@patch('saleor.order.emails.send_payment_confirmation.delay')
def test_handle_fully_paid_order(mock_send_payment_confirmation, order):
    handle_fully_paid_order(order)
    event_order_paid, event_email_sent = order.events.all()
    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID.value

    assert event_email_sent.type == OrderEvents.EMAIL_SENT.value
    assert event_email_sent.parameters == {
        'email': order.get_user_current_email(),
        'email_type': OrderEventsEmails.PAYMENT.value}

    mock_send_payment_confirmation.assert_called_once_with(order.pk)


def test_validate_payment():
    @validate_payment
    def test_function(payment, *args, **kwargs):
        return True

    payment = Mock(is_active=True)
    test_function(payment)

    non_active_payment = Mock(is_active=False)
    with pytest.raises(PaymentError):
        test_function(non_active_payment)


def test_create_payment(settings):
    data = {'gateway': settings.DUMMY}
    payment = create_payment(**data)
    assert payment.gateway == settings.DUMMY

    same_payment = create_payment(**data)
    assert payment == same_payment


def test_create_transaction(transaction_data):
    txn = create_transaction(**transaction_data)

    assert txn.payment == transaction_data['payment']
    assert txn.token == transaction_data['token']
    assert txn.kind == transaction_data['kind']
    assert txn.is_success == transaction_data['is_success']
    assert txn.amount == transaction_data['amount']
    assert txn.gateway_response == transaction_data['gateway_response']

    same_txn = create_transaction(**transaction_data)
    assert txn == same_txn


def test_create_transaction_no_gateway_response(transaction_data):
    transaction_data.pop('gateway_response')
    txn = create_transaction(**transaction_data)
    assert txn.gateway_response == {}


def test_gateway_get_client_token(settings):
    gateway_name = list(settings.PAYMENT_GATEWAYS.keys())[0]
    gateway = settings.PAYMENT_GATEWAYS[gateway_name]
    module = gateway['module']
    with patch('%s.get_client_token' % module) as transaction_token_mock:
        gateway_get_client_token(gateway_name)
        transaction_token_mock.assert_called_once_with()


def test_gateway_get_client_token_not_allowed_gateway(settings):
    gateway = 'example-gateway'
    settings.CHECKOUT_PAYMENT_GATEWAYS = {}
    with pytest.raises(ValueError):
        gateway_get_client_token(gateway)


def test_gateway_get_client_token_not_existing_gateway(settings):
    gateway = 'example-gateway'
    settings.CHECKOUT_PAYMENT_GATEWAYS = {gateway: 'Example gateway'}
    with pytest.raises(ImproperlyConfigured):
        gateway_get_client_token(gateway)


@pytest.mark.parametrize(
    'func', [gateway_authorize, gateway_capture, gateway_refund, gateway_void])
def test_payment_needs_to_be_active_for_any_action(func, payment_dummy):
    payment_dummy.is_active = False
    with pytest.raises(PaymentError) as exc:
        func(payment_dummy, 'token')
    assert exc.value.message == NOT_ACTIVE_PAYMENT_ERROR


def test_gateway_authorize_errors(payment_dummy):
    payment_dummy.charge_status = ChargeStatus.CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_authorize(payment_dummy, 'payment-token')
    assert exc.value.message == (
        'Charged transactions cannot be authorized again.')


@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_authorize(
        mock_get_payment_gateway, payment_txn_preauth, gateway_params,
        transaction_token):
    payment_token = transaction_token
    txn = payment_txn_preauth.transactions.first()
    payment = payment_txn_preauth

    mock_authorize = Mock(return_value=(txn, ''))
    mock_get_payment_gateway.return_value = (
        Mock(authorize=mock_authorize), gateway_params)

    gateway_authorize(payment, payment_token)
    mock_get_payment_gateway.assert_called_once_with(payment.gateway)
    mock_authorize.assert_called_once_with(
        payment, payment_token, **gateway_params)


@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_authorize_failed(
        mock_get_payment_gateway, payment_txn_preauth, gateway_params,
        transaction_token):
    payment_token = transaction_token
    txn = payment_txn_preauth.transactions.first()
    txn.is_success = False
    payment = payment_txn_preauth

    mock_authorize = Mock(return_value=(txn, EXAMPLE_ERROR))
    mock_get_payment_gateway.return_value = (
        Mock(authorize=mock_authorize), gateway_params)
    with pytest.raises(PaymentError) as exc:
        gateway_authorize(payment, payment_token)
    assert exc.value.message == EXAMPLE_ERROR


@patch('saleor.payment.utils.handle_fully_paid_order')
@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_capture(
        mock_get_payment_gateway, mock_handle_fully_paid_order, payment_txn_preauth,
        gateway_params):
    txn = payment_txn_preauth.transactions.first()
    payment = payment_txn_preauth
    assert not payment.captured_amount
    amount = payment.total

    mock_capture = Mock(return_value=(txn, ''))
    mock_get_payment_gateway.return_value = (
        Mock(capture=mock_capture), gateway_params)

    gateway_capture(payment, amount)
    mock_get_payment_gateway.assert_called_once_with(payment.gateway)
    mock_capture.assert_called_once_with(
        payment, amount=amount, **gateway_params)

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.CHARGED
    assert payment.captured_amount == payment.total
    mock_handle_fully_paid_order.assert_called_once_with(payment.order)


@patch('saleor.payment.utils.handle_fully_paid_order')
@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_capture_partial_capture(
        mock_get_payment_gateway, mock_handle_fully_paid_order, payment_txn_preauth,
        gateway_params, settings):
    payment = payment_txn_preauth
    amount = payment.total * Decimal('0.5')
    txn = payment.transactions.first()
    txn.amount = amount
    txn.currency = settings.DEFAULT_CURRENCY

    mock_capture = Mock(return_value=(txn, ''))
    mock_get_payment_gateway.return_value = (
        Mock(capture=mock_capture), gateway_params)

    gateway_capture(payment, amount)

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.CHARGED
    assert payment.captured_amount == amount
    assert payment.currency == settings.DEFAULT_CURRENCY
    assert not mock_handle_fully_paid_order.called


@patch('saleor.payment.utils.handle_fully_paid_order')
@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_capture_failed(
        mock_get_payment_gateway, mock_handle_fully_paid_order, payment_txn_preauth,
        gateway_params):
    txn = payment_txn_preauth.transactions.first()
    txn.is_success = False

    payment = payment_txn_preauth
    amount = payment.total

    mock_capture = Mock(return_value=(txn, EXAMPLE_ERROR))
    mock_get_payment_gateway.return_value = (
        Mock(capture=mock_capture), gateway_params)
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment, amount)
    assert exc.value.message == EXAMPLE_ERROR
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert not payment.captured_amount
    assert not mock_handle_fully_paid_order.called


def test_gateway_capture_errors(payment_dummy):
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment_dummy, Decimal('0'))
    assert exc.value.message == 'Amount should be a positive number.'

    payment_dummy.charge_status = ChargeStatus.FULLY_REFUNDED
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment_dummy, Decimal('10'))
    assert exc.value.message == 'This payment cannot be captured.'

    payment_dummy.charge_status = ChargeStatus.NOT_CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment_dummy, Decimal('1000000'))
    assert exc.value.message == (
        'Unable to capture more than authorized amount.')


@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_void(mock_get_payment_gateway, payment_txn_preauth, gateway_params):
    txn = payment_txn_preauth.transactions.first()
    payment = payment_txn_preauth
    assert payment.is_active

    mock_void = Mock(return_value=(txn, ''))
    mock_get_payment_gateway.return_value = (Mock(void=mock_void), gateway_params)

    gateway_void(payment)
    mock_get_payment_gateway.assert_called_once_with(payment.gateway)
    mock_void.assert_called_once_with(payment, **gateway_params)

    payment.refresh_from_db()
    assert payment.is_active == False


@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_void_failed(
        mock_get_payment_gateway, payment_txn_preauth, gateway_params):
    txn = payment_txn_preauth.transactions.first()
    txn.is_success = False
    payment = payment_txn_preauth

    mock_void = Mock(return_value=(txn, EXAMPLE_ERROR))
    mock_get_payment_gateway.return_value = (Mock(void=mock_void), gateway_params)
    with pytest.raises(PaymentError) as exc:
        gateway_void(payment)
    assert exc.value.message == EXAMPLE_ERROR

    payment.refresh_from_db()
    assert payment.is_active


def test_gateway_void_errors(payment_dummy):
    payment_dummy.charge_status = ChargeStatus.CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_void(payment_dummy)
    exc.value.message == 'Only pre-authorized transactions can be voided.'


@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_refund(
        mock_get_payment_gateway, payment_txn_captured, gateway_params):
    txn = payment_txn_captured.transactions.first()
    payment = payment_txn_captured
    amount = payment.total

    mock_refund = Mock(return_value=(txn, ''))
    mock_get_payment_gateway.return_value = (
        Mock(refund=mock_refund), gateway_params)

    gateway_refund(payment, amount)
    mock_get_payment_gateway.assert_called_once_with(payment.gateway)
    mock_refund.assert_called_once_with(payment, amount, **gateway_params)

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert not payment.captured_amount


@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_refund_partial_refund(
        mock_get_payment_gateway, payment_txn_captured, gateway_params, settings):
    payment = payment_txn_captured
    amount = payment.total * Decimal('0.5')
    txn = payment_txn_captured.transactions.first()
    txn.amount = amount
    txn.currency = settings.DEFAULT_CURRENCY

    mock_refund = Mock(return_value=(txn, ''))
    mock_get_payment_gateway.return_value = (
        Mock(refund=mock_refund), gateway_params)

    gateway_refund(payment, amount)

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.CHARGED
    assert payment.captured_amount == payment.total - amount


@patch('saleor.payment.utils.get_payment_gateway')
def test_gateway_refund_failed(
        mock_get_payment_gateway, payment_txn_captured, gateway_params, settings):
    txn = payment_txn_captured.transactions.first()
    payment = payment_txn_captured
    captured_before = payment.captured_amount
    txn.is_success = False

    mock_refund = Mock(return_value=(txn, EXAMPLE_ERROR))
    mock_get_payment_gateway.return_value = (
        Mock(refund=mock_refund), gateway_params)

    with pytest.raises(PaymentError) as exc:
        gateway_refund(payment, Decimal('10.00'))
    exc.value.message == EXAMPLE_ERROR
    payment.refresh_from_db()
    assert payment.captured_amount == captured_before


def test_gateway_refund_errors(payment_txn_captured):
    payment = payment_txn_captured
    with pytest.raises(PaymentError) as exc:
        gateway_refund(payment, Decimal('1000000'))
    assert exc.value.message == 'Cannot refund more than captured'

    with pytest.raises(PaymentError) as exc:
        gateway_refund(payment, Decimal('0'))
    assert exc.value.message == 'Amount should be a positive number.'

    payment.charge_status = ChargeStatus.NOT_CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_refund(payment, Decimal('1'))
    assert exc.value.message == 'This payment cannot be captured.'


def test_payment_provider_templates_exists(payment_dummy):
    # FIXME test if for each payment provider there's corresponding
    # module and template for the old checkout
    pass
