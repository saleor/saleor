import logging
from decimal import Decimal
from typing import Dict, List, Tuple

import braintree as braintree_sdk
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import pgettext_lazy
from prices import Money

from .forms import BraintreePaymentForm

logger = logging.getLogger(__name__)

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


def get_customer_data(payment: Dict) -> Dict:
    return {
        'order_id': payment['order'],
        'billing': {
            'first_name': payment['billing_first_name'],
            'last_name': payment['billing_last_name'],
            'company': payment['billing_company_name'],
            'postal_code': payment['billing_postal_code'],
            'street_address': payment['billing_address_1'],
            'extended_address': payment['billing_address_2'],
            "locality": payment['billing_city'],
            'region': payment['billing_country_area'],
            'country_code_alpha2': payment['billing_country_code']},
        'risk_data': {
            'customer_ip': payment['customer_ip_address'] or ''},
        'customer': {
            'email': payment['billing_email']}}


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
    if bt_transaction.currency_iso_code != settings.DEFAULT_CURRENCY:
        logger.error(
            'Braintree\'s currency is different than shop\'s currency')
    # FIXME we should have a predefined list of fields that will be supported
    # in the API
    gateway_response = {
        'transaction_id': getattr(bt_transaction, 'id', ''),
        'currency': bt_transaction.currency_iso_code,
        'amount': bt_transaction.amount,  # Decimal type
        'credit_card': bt_transaction.credit_card,
        'errors': errors}
    return gateway_response


def get_template():
    return 'order/payment/braintree.html'


def get_form_class():
    return BraintreePaymentForm


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


def get_client_token(**connection_params: Dict) -> str:
    gateway = get_braintree_gateway(**connection_params)
    client_token = gateway.client_token.generate()
    return client_token


def process_payment(
        payment: Dict, payment_token: str, amount: Decimal,
        **connection_params: Dict) -> Dict:
    auth_resp = authorize(payment, payment_token, **connection_params)
    transaction_token = auth_resp['transaction_id']

    try:
        return capture(transaction_token, amount, **connection_params)
    except Exception as e:
        void(transaction_token, **connection_params)


def authorize(
        payment: Dict, payment_token: str, **connection_params: Dict) -> Dict:
    gateway = get_braintree_gateway(**connection_params)

    try:
        result = gateway.transaction.sale({
            'amount': str(payment['total']),
            'payment_method_nonce': payment_token,
            'options': {
                'submit_for_settlement': CONFIRM_MANUALLY,
                'three_d_secure': {
                    'required': THREE_D_SECURE_REQUIRED}},
            **get_customer_data(payment)})
    except braintree_sdk.exceptions.NotFoundError:
        # FIXME: make this a payment generic exception
        raise Exception('Unable to process the transaction. '
            'Transaction\'s token is incorrect or expired.')

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    return {
        'is_success': result.is_success,
        'transaction_id': gateway_response['transaction_id'],
        'gateway_response': gateway_response,
        'errors': error,
    }


def capture(
        payment: Dict, payment_token: str, amount: Decimal,
        **connection_params: Dict) -> Dict:
    gateway = get_braintree_gateway(**connection_params)

    try:
        result = gateway.transaction.submit_for_settlement(
            transaction_id=payment_token, amount=str(amount))
    except braintree_sdk.exceptions.NotFoundError:
        raise Exception('Unable to process the transaction. '
            'Transaction\'s token is incorrect or expired.')

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    return {
        'is_success': result.is_success,
        'transaction_id': gateway_response['transaction_id'],
        'gateway_response': gateway_response,
        'errors': error,
    }


def void(
        payment: Dict, payment_token: str, **connection_params: Dict) -> Dict:
    gateway = get_braintree_gateway(**connection_params)

    try:
        result = gateway.transaction.void(transaction_id=payment_token)
    except braintree_sdk.exceptions.NotFoundError:
        raise Exception('Unable to process the transaction. '
            'Transaction\'s token is incorrect or expired.')

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    return {
        'is_success': result.is_success,
        'transaction_id': gateway_response['transaction_id'],
        'gateway_response': gateway_response,
        'errors': error,
    }


def refund(
        payment: Dict, payment_token: str, amount: Decimal,
        **connection_params: Dict) -> Dict:
    gateway = get_braintree_gateway(**connection_params)

    try:
        result = gateway.transaction.refund(
            transaction_id=payment_token,
            amount_or_options=str(amount))
    except braintree_sdk.exceptions.NotFoundError:
        raise Exception('Unable to process the transaction. '
            'Transaction\'s token is incorrect or expired.')

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    return {
        'is_success': result.is_success,
        'transaction_id': gateway_response['transaction_id'],
        'gateway_response': gateway_response,
        'errors': error,
    }
