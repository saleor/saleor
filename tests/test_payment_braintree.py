import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from braintree import Environment, ErrorResult, SuccessfulResult, Transaction
from braintree.errors import Errors
from braintree.exceptions import NotFoundError
from braintree.validation_error import ValidationError
from django.core.exceptions import ImproperlyConfigured
from prices import Money

from saleor.payment import TransactionType
from saleor.payment.providers.braintree import (
    CONFIRM_MANUALLY, THREE_D_SECURE_REQUIRED, authorize, capture,
    extract_gateway_response, get_transaction_token, get_customer_data,
    get_error_for_client, get_gateway, refund,
    transaction_and_incorrect_token_error, void)

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
            amount='0.20',
            created_at='2018-10-20 18:34:22',
            credit_card={
                'token': None,
                'bin': '400000',
                'last_4': '0002',
                'card_type': 'Visa',
                'expiration_month': '01',
                'expiration_year': '2020',
                'customer_location': 'International'},
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


def test_get_customer_data(payment_dummy):
    payment = payment_dummy
    result = get_customer_data(payment)
    expected_result = {
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
        'saleor.payment.providers.braintree.ERROR_CODES_WHITELIST', [])
    assert get_error_for_client([error]) == DEFAULT_ERROR

    monkeypatch.setattr(
        'saleor.payment.providers.braintree.ERROR_CODES_WHITELIST',
        [braintree_error.code])
    assert get_error_for_client([error]) == braintree_error.message


def test_extract_gateway_response(braintree_success_response):
    result = extract_gateway_response(braintree_success_response)
    t = braintree_success_response.transaction
    expected_result = {
        'currency_iso_code': t.currency_iso_code,
        'amount': str(t.amount),
        'created_at': str(t.created_at),
        'credit_card': t.credit_card,
        'additional_processor_response': t.additional_processor_response,
        'gateway_rejection_reason': t.gateway_rejection_reason,
        'processor_response_code': t.processor_response_code,
        'processor_response_text': t.processor_response_text,
        'processor_settlement_response_code': t.processor_settlement_response_code,  # noqa
        'processor_settlement_response_text': t.processor_settlement_response_text,  # noqa
        'risk_data': t.risk_data,
        'status': t.status,
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
def test_get_gateway(gateway_config):
    result = get_gateway(**gateway_config)
    assert gateway_config['sandbox_mode'] == False
    assert result.config.environment == Environment.Production
    assert result.config.merchant_id == gateway_config['merchant_id']
    assert result.config.public_key == gateway_config['public_key']
    assert result.config.private_key == gateway_config['private_key']


@pytest.mark.integration
def test_get_gateway_sandbox(gateway_config):
    gateway_config['sandbox_mode'] = True
    result = get_gateway(**gateway_config)
    assert result.config.environment == Environment.Sandbox


def test_get_gateway_inproperly_configured(gateway_config):
    with pytest.raises(ImproperlyConfigured):
        gateway_config['private_key'] = None
        get_gateway(**gateway_config)


@patch('saleor.payment.providers.braintree.get_gateway')
def test_get_transaction_token(mock_gateway, gateway_config):
    transaction_token = 'transaction-token'
    mock_generate = Mock(return_value='transaction-token')
    mock_gateway.return_value = Mock(client_token=Mock(generate=mock_generate))
    result = get_transaction_token(**gateway_config)
    mock_gateway.assert_called_once_with(**gateway_config)
    mock_generate.assert_called_once_with()
    assert result == transaction_token


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.get_gateway')
def test_authorize_error_response(
        mock_gateway, payment_dummy, braintree_error_response):
    payment = payment_dummy
    token = 'example-token'
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))
    txn, error = authorize(payment, token)

    assert txn.gateway_response == extract_gateway_response(
        braintree_error_response)
    assert not txn.is_success
    assert error == DEFAULT_ERROR



@pytest.mark.integration
@patch('saleor.payment.providers.braintree.transaction_and_incorrect_token_error')
@patch('saleor.payment.providers.braintree.get_gateway')
def test_authorize_incorrect_token(
        mock_gateway, mock_transaction, payment_dummy,
        braintree_not_found_error):
    payment = payment_dummy
    token = 'example-token'
    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))
    expected_result = ('txn', 'error')
    mock_transaction.return_value = expected_result
    result = authorize(payment, token)
    assert result == expected_result
    mock_transaction.assert_called_once_with(
        payment, type=TransactionType.AUTH, token=token)


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.get_gateway')
def test_authorize(
        mock_gateway, payment_dummy, braintree_success_response):
    payment = payment_dummy
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))
    txn, error = authorize(payment, 'transaction-token')
    assert not error

    assert txn.payment == payment
    assert txn.transaction_type == TransactionType.AUTH
    assert txn.amount == payment.total
    assert txn.gateway_response == extract_gateway_response(
        braintree_success_response)
    assert txn.token == braintree_success_response.transaction.id
    assert txn.is_success == braintree_success_response.is_success

    mock_response.assert_called_once_with({
        'amount': str(payment.total.amount),
        'payment_method_nonce': 'transaction-token',
        'options': {
            'submit_for_settlement': CONFIRM_MANUALLY,
            'three_d_secure': {
                'required': THREE_D_SECURE_REQUIRED}},
        **get_customer_data(payment)})


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.get_gateway')
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
    assert txn.transaction_type == TransactionType.REFUND
    assert txn.amount == Money(amount, settings.DEFAULT_CURRENCY)
    assert txn.gateway_response == extract_gateway_response(
        braintree_success_response)
    assert txn.token == braintree_success_response.transaction.id
    assert txn.is_success == braintree_success_response.is_success

    capture_txn = payment.transactions.filter(
        transaction_type=TransactionType.CAPTURE).first()
    mock_response.assert_called_once_with(
        amount_or_options=str(amount), transaction_token=capture_txn.token)


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.transaction_and_incorrect_token_error')
@patch('saleor.payment.providers.braintree.get_gateway')
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
        transaction_type=TransactionType.CAPTURE).first()
    mock_transaction.assert_called_once_with(
        payment, type=TransactionType.REFUND, token=capture_txn.token,
        amount=amount)


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.get_gateway')
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
    assert error == DEFAULT_ERROR


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.get_gateway')
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
    assert txn.transaction_type == TransactionType.CAPTURE
    assert txn.amount == Money(amount, settings.DEFAULT_CURRENCY)
    assert txn.gateway_response == extract_gateway_response(
        braintree_success_response)
    assert txn.token == braintree_success_response.transaction.id
    assert txn.is_success == braintree_success_response.is_success

    auth_txn = payment.transactions.filter(
        transaction_type=TransactionType.AUTH).first()
    mock_response.assert_called_once_with(
        amount=str(amount), transaction_id=auth_txn.token)


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.transaction_and_incorrect_token_error')
@patch('saleor.payment.providers.braintree.get_gateway')
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
        transaction_type=TransactionType.AUTH).first()
    mock_transaction.assert_called_once_with(
        payment, type=TransactionType.CAPTURE, token=auth_txn.token,
        amount=amount)


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.get_gateway')
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
    assert error == DEFAULT_ERROR



@pytest.mark.integration
@patch('saleor.payment.providers.braintree.get_gateway')
def test_void(
        mock_gateway, payment_txn_preauth, braintree_success_response):
    payment = payment_txn_preauth
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(void=mock_response))
    txn, error = void(payment)
    assert not error

    assert txn.payment == payment
    assert txn.transaction_type == TransactionType.VOID
    assert txn.amount == payment.total
    assert txn.gateway_response == extract_gateway_response(
        braintree_success_response)
    assert txn.token == braintree_success_response.transaction.id
    assert txn.is_success == braintree_success_response.is_success

    auth_txn = payment.transactions.filter(
        transaction_type=TransactionType.AUTH).first()
    mock_response.assert_called_once_with(transaction_token=auth_txn.token)


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.transaction_and_incorrect_token_error')
@patch('saleor.payment.providers.braintree.get_gateway')
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
        transaction_type=TransactionType.AUTH).first()
    mock_transaction.assert_called_once_with(
        payment, type=TransactionType.VOID, token=auth_txn.token)


@pytest.mark.integration
@patch('saleor.payment.providers.braintree.get_gateway')
def test_void_error_response(
        mock_gateway, payment_txn_preauth, braintree_error_response):
    payment = payment_txn_preauth
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(void=mock_response))
    txn, error = void(payment)

    assert txn.gateway_response == extract_gateway_response(
        braintree_error_response)
    assert not txn.is_success
    assert error == DEFAULT_ERROR


def test_transaction_and_incorrect_token_error_helper(payment_dummy, settings):
    amount = Decimal('10.00')
    txn, error = transaction_and_incorrect_token_error(
        payment_dummy, 'example-token', TransactionType.AUTH, amount=amount)
    assert error == INCORRECT_TOKEN_ERROR
    assert not txn.is_success
    assert txn.transaction_type == TransactionType.AUTH
    assert txn.token == 'example-token'
    assert not txn.gateway_response
    assert txn.amount == Money(amount, settings.DEFAULT_CURRENCY)


def test_transaction_and_incorrect_token_error_helper_no_amount(payment_dummy):
    txn, error = transaction_and_incorrect_token_error(
        payment_dummy, 'example-token', TransactionType.AUTH)
    assert txn.amount == payment_dummy.total
