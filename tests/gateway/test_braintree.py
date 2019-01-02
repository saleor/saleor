import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from braintree import (
    CreditCard, Environment, ErrorResult, SuccessfulResult, Transaction)
from braintree.errors import Errors
from braintree.exceptions import NotFoundError
from braintree.validation_error import ValidationError
from django.core.exceptions import ImproperlyConfigured
from prices import Money

from saleor.payment import TransactionKind, get_payment_gateway
from saleor.payment.gateways.braintree import (
    CONFIRM_MANUALLY, THREE_D_SECURE_REQUIRED, authorize, capture,
    extract_gateway_response, get_braintree_gateway, get_client_token,
    get_customer_data, get_error_for_client, refund, void)
from saleor.payment.gateways.braintree.forms import BraintreePaymentForm

INCORRECT_TOKEN_ERROR = (
    'Unable to process the transaction. Transaction\'s token is incorrect '
    'or expired.')
DEFAULT_ERROR = 'Unable to process transaction. Please try again in a moment'


@pytest.fixture
def braintree_success_response():
    return Mock(
        spec=SuccessfulResult,
        is_success=True,
        transaction=Mock(
            id='1x02131',
            spec=Transaction,
            amount=Decimal('0.20'),
            created_at='2018-10-20 18:34:22',
            credit_card='',  # FIXME we should provide a proper CreditCard mock
            additional_processor_response='',
            gateway_rejection_reason='',
            processor_response_code='1000',
            processor_response_text='Approved',
            processor_settlement_response_code='',
            processor_settlement_response_text='',
            risk_data='',
            currency_iso_code='EUR',
            status='authorized'))


@pytest.fixture
def braintree_error():
    return Mock(
        spec=ValidationError,
        code='91507',
        attribute='base',
        message='Cannot submit for settlement unless status is authorized.')


@pytest.fixture
def braintree_error_response(braintree_error):
    return Mock(
        spec=ErrorResult,
        is_success=False,
        transaction=None,
        errors=Mock(
            spec=Errors,
            deep_errors=[braintree_error]))


@pytest.fixture
def braintree_not_found_error():
    return Mock(side_effect=NotFoundError)


@pytest.fixture
def gateway_config():
    return {
        'sandbox_mode': False,
        'merchant_id': '123',
        'public_key': '456',
        'private_key': '789'}


def success_gateway_response(gateway_response):
    data = extract_gateway_response(gateway_response)
    data.pop('currency')
    data.pop('amount')
    return data


def test_get_customer_data(payment_dummy):
    payment = payment_dummy
    result = get_customer_data(payment)
    expected_result = {
        'order_id': payment.order_id,
        'billing': {
            'first_name': payment.billing_first_name,
            'last_name': payment.billing_last_name,
            'company': payment.billing_company_name,
            'postal_code': payment.billing_postal_code,
            'street_address': payment.billing_address_1[:255],
            'extended_address': payment.billing_address_2[:255],
            "locality": payment.billing_city,
            'region': payment.billing_country_area,
            'country_code_alpha2': payment.billing_country_code},
        'risk_data': {
            'customer_ip': payment.customer_ip_address or ''},
        'customer': {
            'email': payment.billing_email}}
    assert result == expected_result


def test_get_error_for_client(braintree_error, monkeypatch):
    # no error
    assert get_error_for_client([]) == ''

    error = {'code': braintree_error.code, 'message': braintree_error.message}

    # error not whitelisted
    monkeypatch.setattr(
        'saleor.payment.gateways.braintree.ERROR_CODES_WHITELIST', {})
    assert get_error_for_client([error]) == DEFAULT_ERROR

    monkeypatch.setattr(
        'saleor.payment.gateways.braintree.ERROR_CODES_WHITELIST',
        {braintree_error.code: ''})
    assert get_error_for_client([error]) == braintree_error.message

    monkeypatch.setattr(
        'saleor.payment.gateways.braintree.ERROR_CODES_WHITELIST',
        {braintree_error.code: 'Error msg override'})
    assert get_error_for_client([error]) == 'Error msg override'


def test_extract_gateway_response(braintree_success_response):
    result = extract_gateway_response(braintree_success_response)
    t = braintree_success_response.transaction
    expected_result = {
        'currency': t.currency_iso_code,
        'amount': t.amount,
        'credit_card': t.credit_card,
        'errors': []}
    assert result == expected_result


def test_extract_gateway_response_no_transaction(
        braintree_error_response, braintree_error):
    result = extract_gateway_response(braintree_error_response)
    assert result == {
        'errors': [
            {
                'code': braintree_error.code,
                'message': braintree_error.message}]}


@pytest.mark.integration
def test_get_braintree_gateway(gateway_config):
    result = get_braintree_gateway(**gateway_config)
    assert gateway_config['sandbox_mode'] == False
    assert result.config.environment == Environment.Production
    assert result.config.merchant_id == gateway_config['merchant_id']
    assert result.config.public_key == gateway_config['public_key']
    assert result.config.private_key == gateway_config['private_key']


@pytest.mark.integration
def test_get_braintree_gateway_sandbox(gateway_config):
    gateway_config['sandbox_mode'] = True
    result = get_braintree_gateway(**gateway_config)
    assert result.config.environment == Environment.Sandbox


def test_get_braintree_gateway_inproperly_configured(gateway_config):
    with pytest.raises(ImproperlyConfigured):
        gateway_config['private_key'] = None
        get_braintree_gateway(**gateway_config)


@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_get_client_token(mock_gateway, gateway_config):
    client_token = 'client-token'
    mock_generate = Mock(return_value='client-token')
    mock_gateway.return_value = Mock(client_token=Mock(generate=mock_generate))
    result = get_client_token(**gateway_config)
    mock_gateway.assert_called_once_with(**gateway_config)
    mock_generate.assert_called_once_with()
    assert result == client_token


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_authorize_error_response(
        mock_gateway, payment_dummy, braintree_error_response):
    payment = payment_dummy
    payment_token = 'payment-token'
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))
    txn, error = authorize(payment, payment_token)

    assert txn.gateway_response == extract_gateway_response(
        braintree_error_response)
    assert not txn.is_success
    assert txn.amount == payment.total
    assert txn.currency == payment.currency
    assert error == DEFAULT_ERROR


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.transaction_and_incorrect_token_error')
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_authorize_incorrect_token(
        mock_gateway, mock_transaction, payment_dummy,
        braintree_not_found_error):
    payment = payment_dummy
    payment_token = 'payment-token'
    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))
    expected_result = ('txn', 'error')
    mock_transaction.return_value = expected_result
    result = authorize(payment, payment_token)
    assert result == expected_result
    mock_transaction.assert_called_once_with(
        payment, kind=TransactionKind.AUTH, token=payment_token)


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_authorize(
        mock_gateway, payment_dummy, braintree_success_response):
    payment = payment_dummy
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))

    txn, error = authorize(payment, 'authentication-token')
    assert not error

    assert txn.payment == payment
    assert txn.kind == TransactionKind.AUTH
    assert txn.amount == braintree_success_response.transaction.amount
    assert txn.currency == braintree_success_response.transaction.currency_iso_code
    assert txn.gateway_response == success_gateway_response(
        braintree_success_response)
    assert txn.token == braintree_success_response.transaction.id
    assert txn.is_success == braintree_success_response.is_success

    mock_response.assert_called_once_with({
        'amount': str(payment.total),
        'payment_method_nonce': 'authentication-token',
        'options': {
            'submit_for_settlement': CONFIRM_MANUALLY,
            'three_d_secure': {
                'required': THREE_D_SECURE_REQUIRED}},
        **get_customer_data(payment)})


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_refund(
        mock_gateway, payment_txn_captured, braintree_success_response,
        settings):
    payment = payment_txn_captured
    amount = Decimal('10.00')
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(refund=mock_response))
    txn, error = refund(payment, amount)
    assert not error

    assert txn.payment == payment
    assert txn.kind == TransactionKind.REFUND
    assert txn.amount == braintree_success_response.transaction.amount
    assert txn.currency == braintree_success_response.transaction.currency_iso_code
    assert txn.gateway_response == success_gateway_response(
        braintree_success_response)
    assert txn.token == braintree_success_response.transaction.id
    assert txn.is_success == braintree_success_response.is_success

    capture_txn = payment.transactions.filter(
        kind=TransactionKind.CAPTURE).first()
    mock_response.assert_called_once_with(
        amount_or_options=str(amount), transaction_id=capture_txn.token)


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.transaction_and_incorrect_token_error')
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_refund_incorrect_token(
        mock_gateway, mock_transaction, payment_txn_captured,
        braintree_not_found_error):
    payment = payment_txn_captured
    amount = Decimal('10.00')
    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(transaction=Mock(refund=mock_response))
    expected_result = ('txn', 'error')
    mock_transaction.return_value = expected_result
    result = refund(payment, amount)
    assert result == expected_result
    capture_txn = payment.transactions.filter(
        kind=TransactionKind.CAPTURE).first()
    mock_transaction.assert_called_once_with(
        payment, kind=TransactionKind.REFUND, token=capture_txn.token,
        amount=amount)


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_refund_error_response(
        mock_gateway, payment_txn_captured, braintree_error_response):
    payment = payment_txn_captured
    amount = Decimal('10.00')
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(refund=mock_response))
    txn, error = refund(payment, amount)

    assert txn.gateway_response == extract_gateway_response(
        braintree_error_response)
    assert not txn.is_success
    assert txn.amount == amount
    assert txn.currency == payment.currency
    assert error == DEFAULT_ERROR


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_capture(
        mock_gateway, payment_txn_preauth, braintree_success_response,
        settings):
    payment = payment_txn_preauth
    amount = Decimal('10.00')
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(
        transaction=Mock(
            submit_for_settlement=mock_response))
    txn, error = capture(payment, amount)
    assert not error

    assert txn.payment == payment
    assert txn.kind == TransactionKind.CAPTURE
    assert txn.amount == braintree_success_response.transaction.amount
    assert txn.currency == braintree_success_response.transaction.currency_iso_code
    assert txn.gateway_response == success_gateway_response(
        braintree_success_response)
    assert txn.token == braintree_success_response.transaction.id
    assert txn.is_success == braintree_success_response.is_success

    auth_txn = payment.transactions.filter(
        kind=TransactionKind.AUTH).first()
    mock_response.assert_called_once_with(
        amount=str(amount), transaction_id=auth_txn.token)


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.transaction_and_incorrect_token_error')
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_capture_incorrect_token(
        mock_gateway, mock_transaction, payment_txn_preauth,
        braintree_not_found_error):
    payment = payment_txn_preauth
    amount = Decimal('10.00')
    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(
        transaction=Mock(
            submit_for_settlement=mock_response))
    expected_result = ('txn', 'error')
    mock_transaction.return_value = expected_result
    result = capture(payment, amount)
    assert result == expected_result
    auth_txn = payment.transactions.filter(
        kind=TransactionKind.AUTH).first()
    mock_transaction.assert_called_once_with(
        payment, kind=TransactionKind.CAPTURE, token=auth_txn.token,
        amount=amount)


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_capture_error_response(
        mock_gateway, payment_txn_preauth, braintree_error_response):
    payment = payment_txn_preauth
    amount = Decimal('10.00')
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(
        transaction=Mock(submit_for_settlement=mock_response))
    txn, error = capture(payment, amount)

    assert txn.gateway_response == extract_gateway_response(
        braintree_error_response)
    assert not txn.is_success
    assert txn.amount == amount
    assert txn.currency == payment.currency
    assert error == DEFAULT_ERROR


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_void(
        mock_gateway, payment_txn_preauth, braintree_success_response):
    payment = payment_txn_preauth
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(void=mock_response))
    txn, error = void(payment)
    assert not error

    assert txn.payment == payment
    assert txn.kind == TransactionKind.VOID
    assert txn.amount == braintree_success_response.transaction.amount
    assert txn.currency == braintree_success_response.transaction.currency_iso_code
    assert txn.gateway_response == success_gateway_response(
        braintree_success_response)
    assert txn.token == braintree_success_response.transaction.id
    assert txn.is_success == braintree_success_response.is_success

    auth_txn = payment.transactions.filter(
        kind=TransactionKind.AUTH).first()
    mock_response.assert_called_once_with(transaction_id=auth_txn.token)


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.transaction_and_incorrect_token_error')
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_void_incorrect_token(
        mock_gateway, mock_transaction, payment_txn_preauth,
        braintree_not_found_error):
    payment = payment_txn_preauth
    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(transaction=Mock(void=mock_response))
    expected_result = ('txn', 'error')
    mock_transaction.return_value = expected_result
    result = void(payment)
    assert result == expected_result
    auth_txn = payment.transactions.filter(
        kind=TransactionKind.AUTH).first()
    mock_transaction.assert_called_once_with(
        payment, kind=TransactionKind.VOID, token=auth_txn.token)


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_void_error_response(
        mock_gateway, payment_txn_preauth, braintree_error_response):
    payment = payment_txn_preauth
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(void=mock_response))
    txn, error = void(payment)

    assert txn.gateway_response == extract_gateway_response(
        braintree_error_response)
    assert not txn.is_success
    assert txn.amount == payment.total
    assert txn.currency == payment.currency
    assert error == DEFAULT_ERROR


def test_braintree_payment_form_incorrect_amount(payment_dummy):
    amount = Decimal('0.01')
    data = {'amount': amount, 'payment_method_nonce': 'fake-nonce'}
    assert amount != payment_dummy.total

    payment_gateway, gateway_params = get_payment_gateway(
        payment_dummy.gateway)
    form = BraintreePaymentForm(
        data=data, amount=payment_dummy.total, gateway=payment_gateway)
    assert not form.is_valid()
    assert form.non_field_errors


def test_braintree_payment_form(settings, payment_dummy):
    payment = payment_dummy
    payment.gateway = settings.BRAINTREE
    data = {'amount': payment.total, 'payment_method_nonce': 'fake-nonce'}

    form = BraintreePaymentForm(
        data=data, amount=payment.total, currency=payment.currency)
    assert form.is_valid()


def test_get_form_class(settings):
    payment_gateway, gateway_params = get_payment_gateway(settings.BRAINTREE)
    assert payment_gateway.get_form_class() == BraintreePaymentForm
