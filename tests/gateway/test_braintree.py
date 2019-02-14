from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from braintree import (
    CreditCard, Environment, ErrorResult, SuccessfulResult, Transaction)
from braintree.errors import Errors
from braintree.exceptions import NotFoundError
from braintree.validation_error import ValidationError
from django.core.exceptions import ImproperlyConfigured

from saleor.payment.gateways.braintree import (
    CONFIRM_MANUALLY, THREE_D_SECURE_REQUIRED, TransactionKind, authorize,
    capture, create_form, extract_gateway_response, get_braintree_gateway,
    get_client_token, get_customer_data, get_error_for_client, process_payment,
    refund, void)
from saleor.payment.gateways.braintree.errors import (
    DEFAULT_ERROR_MESSAGE, BraintreeException)
from saleor.payment.gateways.braintree.forms import BraintreePaymentForm
from saleor.payment.utils import create_payment_information

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
    payment_info = create_payment_information(payment)
    result = get_customer_data(payment_info)
    expected_result = {
        'order_id': payment.order_id,
        'billing': {
            'first_name': payment.billing_first_name,
            'last_name': payment.billing_last_name,
            'company': payment.billing_company_name,
            'postal_code': payment.billing_postal_code,
            'street_address': payment.billing_address_1[:255],
            'extended_address': payment.billing_address_2[:255],
            'locality': payment.billing_city,
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
        'errors': [],
        'transaction_id': t.id}
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
    result = get_client_token(gateway_config)
    mock_gateway.assert_called_once_with(**gateway_config)
    mock_generate.assert_called_once_with()
    assert result == client_token


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_process_payment_error_response(
        mock_gateway, payment_dummy, braintree_error_response, gateway_config):
    payment = payment_dummy
    payment_token = 'payment-token'
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))

    payment_info = create_payment_information(payment, payment_token)
    response = process_payment(payment_info, gateway_config)

    assert isinstance(response, list)
    auth_resp, void_resp = response

    assert auth_resp['kind'] == TransactionKind.AUTH
    assert void_resp['kind'] == TransactionKind.VOID


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_process_payment(
        mock_gateway, payment_dummy, braintree_success_response,
        gateway_config):
    payment = payment_dummy
    payment_token = 'payment-token'
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))

    payment_info = create_payment_information(payment, payment_token)
    response = process_payment(payment_info, gateway_config)

    assert isinstance(response, list)
    auth_resp, capture_resp = response

    assert auth_resp['kind'] == TransactionKind.AUTH
    assert capture_resp['kind'] == TransactionKind.CAPTURE

@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_authorize_error_response(
        mock_gateway, payment_dummy, braintree_error_response, gateway_config):
    payment = payment_dummy
    payment_token = 'payment-token'
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))

    payment_info = create_payment_information(payment, payment_token)
    response = authorize(payment_info, gateway_config)

    assert response['raw_response'] == extract_gateway_response(braintree_error_response)
    assert not response['is_success']
    assert response['error'] == DEFAULT_ERROR


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_authorize_incorrect_token(
        mock_gateway, payment_dummy, braintree_not_found_error,
        gateway_config):
    payment = payment_dummy
    payment_token = 'payment-token'
    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))

    payment_info = create_payment_information(payment, payment_token)
    with pytest.raises(BraintreeException) as e:
        authorize(payment_info, gateway_config)
    assert str(e.value) == DEFAULT_ERROR_MESSAGE


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_authorize(
        mock_gateway, payment_dummy, braintree_success_response,
        gateway_config):
    payment = payment_dummy
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))

    payment_info = create_payment_information(payment, 'auth-token')
    response = authorize(payment_info, gateway_config)
    assert not response['error']

    assert response['kind'] == TransactionKind.AUTH
    assert response['amount'] == braintree_success_response.transaction.amount
    assert response['currency'] == braintree_success_response.transaction.currency_iso_code
    assert response['transaction_id'] == braintree_success_response.transaction.id
    assert response['is_success'] == braintree_success_response.is_success

    mock_response.assert_called_once_with({
        'amount': str(payment.total),
        'payment_method_nonce': 'auth-token',
        'options': {
            'submit_for_settlement': CONFIRM_MANUALLY,
            'three_d_secure': {
                'required': THREE_D_SECURE_REQUIRED}},
        **get_customer_data(payment_info)})


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_refund(
        mock_gateway, payment_txn_captured, braintree_success_response,
        settings, gateway_config):
    payment = payment_txn_captured
    amount = Decimal('10.00')
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(refund=mock_response))

    payment_info = create_payment_information(payment, 'token', amount)
    response = refund(payment_info, gateway_config)
    assert not response['error']

    assert response['kind'] == TransactionKind.REFUND
    assert response['amount'] == braintree_success_response.transaction.amount
    assert response['currency'] == braintree_success_response.transaction.currency_iso_code
    assert response['transaction_id'] == braintree_success_response.transaction.id
    assert response['is_success'] == braintree_success_response.is_success
    mock_response.assert_called_once_with(
        amount_or_options=str(amount), transaction_id=payment_info['token'])


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_refund_incorrect_token(
        mock_gateway, payment_txn_captured, braintree_not_found_error,
        gateway_config):
    payment = payment_txn_captured
    amount = Decimal('10.00')

    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(transaction=Mock(refund=mock_response))

    payment_info = create_payment_information(payment, 'token', amount)
    with pytest.raises(BraintreeException) as e:
        refund(payment_info, gateway_config)
    assert str(e.value) == DEFAULT_ERROR_MESSAGE


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_refund_error_response(
        mock_gateway, payment_txn_captured, braintree_error_response,
        gateway_config):
    payment = payment_txn_captured
    amount = Decimal('10.00')
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(refund=mock_response))

    payment_info = create_payment_information(payment, 'token', amount)
    response = refund(payment_info, gateway_config)

    assert response['raw_response'] == extract_gateway_response(
        braintree_error_response)
    assert not response['is_success']
    assert response['error'] == DEFAULT_ERROR


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_capture(
        mock_gateway, payment_txn_preauth, braintree_success_response,
        settings, gateway_config):
    payment = payment_txn_preauth
    amount = Decimal('10.00')
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(
        transaction=Mock(submit_for_settlement=mock_response))

    payment_info = create_payment_information(payment, 'token', amount)
    response = capture(payment_info, gateway_config)
    assert not response['error']

    assert response['kind'] == TransactionKind.CAPTURE
    assert response['amount'] == braintree_success_response.transaction.amount
    assert response['currency'] == braintree_success_response.transaction.currency_iso_code
    assert response['transaction_id'] == braintree_success_response.transaction.id
    assert response['is_success'] == braintree_success_response.is_success

    mock_response.assert_called_once_with(
        amount=str(amount), transaction_id=payment_info['token'])


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_capture_incorrect_token(
        mock_gateway, payment_txn_preauth, braintree_not_found_error,
        gateway_config):
    payment = payment_txn_preauth
    amount = Decimal('10.00')
    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(
        transaction=Mock(submit_for_settlement=mock_response))

    payment_info = create_payment_information(payment)
    with pytest.raises(BraintreeException) as e:
        capture(payment_info, gateway_config)
    assert str(e.value) == DEFAULT_ERROR_MESSAGE


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_capture_error_response(
        mock_gateway, payment_txn_preauth, braintree_error_response,
        gateway_config):
    payment = payment_txn_preauth
    amount = Decimal('10.00')
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(
        transaction=Mock(submit_for_settlement=mock_response))

    payment_info = create_payment_information(payment, 'token')
    response = capture(payment_info, gateway_config)

    assert response['raw_response'] == extract_gateway_response(
        braintree_error_response)
    assert not response['is_success']
    assert response['error'] == DEFAULT_ERROR


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_void(
        mock_gateway, payment_txn_preauth, braintree_success_response,
        gateway_config):
    payment = payment_txn_preauth
    mock_response = Mock(return_value=braintree_success_response)
    mock_gateway.return_value = Mock(transaction=Mock(void=mock_response))

    payment_info = create_payment_information(payment, 'token')
    response = void(payment_info, gateway_config)
    assert not response['error']

    assert response['kind'] == TransactionKind.VOID
    assert response['amount'] == braintree_success_response.transaction.amount
    assert response['currency'] == braintree_success_response.transaction.currency_iso_code
    assert response['transaction_id'] == braintree_success_response.transaction.id
    assert response['is_success'] == braintree_success_response.is_success
    mock_response.assert_called_once_with(transaction_id=payment_info['token'])


@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_void_incorrect_token(
        mock_gateway, payment_txn_preauth, braintree_not_found_error,
        gateway_config):
    payment = payment_txn_preauth

    mock_response = Mock(side_effect=braintree_not_found_error)
    mock_gateway.return_value = Mock(transaction=Mock(void=mock_response))

    payment_info = create_payment_information(payment)
    with pytest.raises(BraintreeException) as e:
        void(payment_info, gateway_config)
    assert str(e.value) == DEFAULT_ERROR_MESSAGE

@pytest.mark.integration
@patch('saleor.payment.gateways.braintree.get_braintree_gateway')
def test_void_error_response(
        mock_gateway, payment_txn_preauth, braintree_error_response,
        gateway_config):
    payment = payment_txn_preauth
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(void=mock_response))

    payment_info = create_payment_information(payment)
    response = void(payment_info, gateway_config)

    assert response['raw_response'] == extract_gateway_response(
        braintree_error_response)
    assert not response['is_success']
    assert response['error'] == DEFAULT_ERROR


def test_braintree_payment_form_incorrect_amount(payment_dummy):
    amount = Decimal('0.01')
    data = {'amount': amount, 'payment_method_nonce': 'fake-nonce'}
    assert amount != payment_dummy.total
    payment_info = create_payment_information(payment_dummy)

    form = BraintreePaymentForm(data=data, payment_information=payment_info)
    assert not form.is_valid()
    assert form.non_field_errors


def test_braintree_payment_form(payment_dummy):
    payment = payment_dummy

    data = {'amount': payment.total, 'payment_method_nonce': 'fake-nonce'}
    payment_info = create_payment_information(payment)

    form = create_form(
        data=data, payment_information=payment_info,
        connection_params={'secret': '123'})

    assert isinstance(form, BraintreePaymentForm)
    assert form.is_valid()
