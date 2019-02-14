import logging
from typing import Dict, List

import braintree as braintree_sdk
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import pgettext_lazy

from .errors import DEFAULT_ERROR_MESSAGE, BraintreeException
from .forms import BraintreePaymentForm

logger = logging.getLogger(__name__)

TEMPLATE_PATH = 'order/payment/braintree.html'

# FIXME: Move to SiteSettings

# If this option is checked, then one needs to authorize the amount paid
# manually via the Braintree Dashboard
CONFIRM_MANUALLY = False
THREE_D_SECURE_REQUIRED = False

# Error codes whitelist should be a dict of code: error_msg_override
# if no error_msg_override is provided,
# then error message returned by the gateway will be used
ERROR_CODES_WHITELIST = {
    '91506': """
        Cannot refund transaction unless it is settled.
        Please try again later. Settlement time might vary depending
        on the issuers bank.""",
}


class TransactionKind:
    AUTH = 'auth'
    CAPTURE = 'capture'
    CHARGE = 'charge'
    REFUND = 'refund'
    VOID = 'void'


def get_customer_data(payment_information: Dict) -> Dict:
    billing = payment_information['billing']
    return {
        'order_id': payment_information['order_id'],
        'billing': {
            'first_name': billing['first_name'],
            'last_name': billing['last_name'],
            'company': billing['company_name'],
            'postal_code': billing['postal_code'],
            'street_address': billing['street_address_1'],
            'extended_address': billing['street_address_2'],
            'locality': billing['city'],
            'region': billing['country_area'],
            'country_code_alpha2': billing['country']},
        'risk_data': {
            'customer_ip': payment_information['customer_ip_address'] or ''},
        'customer': {'email': payment_information['customer_email']}}


def get_error_for_client(errors: List) -> str:
    """Filters all error messages and decides which one is visible for the
    client side.
    """
    if not errors:
        return ''
    default_msg = pgettext_lazy(
        'payment error',
        'Unable to process transaction. Please try again in a moment')
    for error in errors:
        if error['code'] in ERROR_CODES_WHITELIST:
            return ERROR_CODES_WHITELIST[error['code']] or error['message']
    return default_msg


def extract_gateway_response(braintree_result) -> Dict:
    """Extract data from Braintree response that will be stored locally."""
    errors = []
    if not braintree_result.is_success:
        errors = [
            {'code': error.code, 'message': error.message}
            for error in braintree_result.errors.deep_errors]

    bt_transaction = braintree_result.transaction
    if not bt_transaction:
        return {'errors': errors}

    return {
        'transaction_id': getattr(bt_transaction, 'id', ''),
        'currency': bt_transaction.currency_iso_code,
        'amount': bt_transaction.amount,  # Decimal type
        'credit_card': bt_transaction.credit_card,
        'errors': errors}


def create_form(data, payment_information, connection_params):
    return BraintreePaymentForm(
        data=data, payment_information=payment_information)


def get_braintree_gateway(sandbox_mode, merchant_id, public_key, private_key):
    if not all([merchant_id, private_key, public_key]):
        raise ImproperlyConfigured('Incorrectly configured Braintree gateway.')
    environment = braintree_sdk.Environment.Sandbox
    if not sandbox_mode:
        environment = braintree_sdk.Environment.Production

    config = braintree_sdk.Configuration(
        environment=environment,
        merchant_id=merchant_id,
        public_key=public_key,
        private_key=private_key)
    gateway = braintree_sdk.BraintreeGateway(config=config)
    return gateway


def get_client_token(connection_params: Dict) -> str:
    gateway = get_braintree_gateway(**connection_params)
    client_token = gateway.client_token.generate()
    return client_token


def authorize(payment_information: Dict, connection_params: Dict) -> Dict:
    gateway = get_braintree_gateway(**connection_params)

    try:
        result = gateway.transaction.sale({
            'amount': str(payment_information['amount']),
            'payment_method_nonce': payment_information['token'],
            'options': {
                'submit_for_settlement': CONFIRM_MANUALLY,
                'three_d_secure': {
                    'required': THREE_D_SECURE_REQUIRED}},
            **get_customer_data(payment_information)})
    except braintree_sdk.exceptions.NotFoundError:
        raise BraintreeException(DEFAULT_ERROR_MESSAGE)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    return {
        'is_success': result.is_success,
        'kind': TransactionKind.AUTH,
        'amount': gateway_response.get(
            'amount', payment_information['amount']),
        'currency': gateway_response.get(
            'currency', payment_information['currency']),
        'transaction_id': gateway_response.get(
            'transaction_id', payment_information['token']),
        'error': error,
        'raw_response': gateway_response}


def capture(payment_information: Dict, connection_params: Dict) -> Dict:
    gateway = get_braintree_gateway(**connection_params)

    try:
        result = gateway.transaction.submit_for_settlement(
            transaction_id=payment_information['token'],
            amount=str(payment_information['amount']))
    except braintree_sdk.exceptions.NotFoundError:
        raise BraintreeException(DEFAULT_ERROR_MESSAGE)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    return {
        'is_success': result.is_success,
        'kind': TransactionKind.CAPTURE,
        'amount': gateway_response.get(
            'amount', payment_information['amount']),
        'currency': gateway_response.get(
            'currency', payment_information['currency']),
        'transaction_id': gateway_response.get(
            'transaction_id', payment_information['token']),
        'error': error,
        'raw_response': gateway_response}


def void(payment_information: Dict, connection_params: Dict) -> Dict:
    gateway = get_braintree_gateway(**connection_params)

    try:
        result = gateway.transaction.void(
            transaction_id=payment_information['token'])
    except braintree_sdk.exceptions.NotFoundError:
        raise BraintreeException(DEFAULT_ERROR_MESSAGE)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    return {
        'is_success': result.is_success,
        'kind': TransactionKind.VOID,
        'amount': gateway_response.get(
            'amount', payment_information['amount']),
        'currency': gateway_response.get(
            'currency', payment_information['currency']),
        'transaction_id': gateway_response.get(
            'transaction_id', payment_information['token']),
        'error': error,
        'raw_response': gateway_response}


def refund(payment_information: Dict, connection_params: Dict) -> Dict:
    gateway = get_braintree_gateway(**connection_params)

    try:
        result = gateway.transaction.refund(
            transaction_id=payment_information['token'],
            amount_or_options=str(payment_information['amount']))
    except braintree_sdk.exceptions.NotFoundError:
        raise BraintreeException(DEFAULT_ERROR_MESSAGE)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    return {
        'is_success': result.is_success,
        'kind': TransactionKind.REFUND,
        'amount': gateway_response.get(
            'amount', payment_information['amount']),
        'currency': gateway_response.get(
            'currency', payment_information['currency']),
        'transaction_id': gateway_response.get(
            'transaction_id', payment_information['token']),
        'error': error,
        'raw_response': gateway_response}


def process_payment(
        payment_information: Dict, connection_params: Dict) -> Dict:
    auth_resp = authorize(payment_information, connection_params)
    if auth_resp['is_success']:
        payment_information['token'] = auth_resp['transaction_id']
        return [auth_resp, capture(payment_information, connection_params)]
    return [auth_resp, void(payment_information, connection_params)]
