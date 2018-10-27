import logging
from decimal import Decimal
from typing import Dict, List, Tuple

import braintree as braintree_sdk
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import pgettext_lazy
from prices import Money

from ... import Transactions
from ...models import Payment, Transaction
from ...utils import create_transaction

logger = logging.getLogger(__name__)
# FIXME: Move to SiteSettings

# If this option is checked, then one needs to authorize the amount paid
# manually via the Braintree Dashboard
CONFIRM_MANUALLY = False
THREE_D_SECURE_REQUIRED = False

# FIXME: Provide list of visible errors and messages translations
# FIXME: We should also store universal visible errors for all payment
# gateways, and parse gateway-specific errors to the unified version

# Error codes whitelist should be a dict of code: error_msg_override
# if no error_msg_override is provided,
# then error message returned by the gateway will be used
ERROR_CODES_WHITELIST = {
    '91506': """
        Cannot refund transaction unless it is settled.
        Please try again later. Settlement time might vary depending
        on the issuers bank.""",
}


def get_customer_data(payment: Payment) -> Dict:
    return {
        "order_id": payment.order_id,
        'billing': {
            'first_name': payment.billing_first_name,
            'last_name': payment.billing_last_name,
            'company': payment.billing_company_name,
            'postal_code': payment.billing_postal_code,
            'street_address': payment.billing_address_1,
            'extended_address': payment.billing_address_2,
            "locality": payment.billing_city,
            'region': payment.billing_country_area,
            'country_code_alpha2': payment.billing_country_code},
        'risk_data': {
            'customer_ip': payment.customer_ip_address or ''},
        'customer': {
            'email': payment.billing_email}}


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


def transaction_and_incorrect_token_error(
        payment: Payment,
        token: str,
        type: Transactions,
        amount: Decimal = None) -> Tuple[Transaction, str]:
    amount = amount or payment.total
    txn = create_transaction(
        payment=payment,
        kind=type,
        currency=payment.currency,
        amount=amount,
        gateway_response={},
        token=token,
        is_success=False)
    error = (
        'Unable to process the transaction. Transaction\'s token is incorrect '
        'or expired.')
    return txn, error


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
        'currency': bt_transaction.currency_iso_code,
        'amount': bt_transaction.amount,  # Decimal type
        'credit_card': bt_transaction.credit_card,
        'errors': errors}
    return gateway_response


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


def authorize(
        payment: Payment,
        payment_token: str,
        **connection_params: Dict) -> Tuple[Transaction, str]:
    gateway = get_braintree_gateway(**connection_params)
    try:
        result = gateway.transaction.sale({
            'amount': str(payment.total),
            'payment_method_nonce': payment_token,
            'options': {
                'submit_for_settlement': CONFIRM_MANUALLY,
                'three_d_secure': {
                    'required': THREE_D_SECURE_REQUIRED}},
            **get_customer_data(payment)})
    except braintree_sdk.exceptions.NotFoundError:
        return transaction_and_incorrect_token_error(
            payment, type=Transactions.AUTH, token=payment_token)
    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])
    credit_card_data = gateway_response.pop('credit_cart')
    if credit_card_data:
        payment.cc_first_digits = credit_card_data.bin
        payment.cc_last_digits = credit_card_data.last_4
        payment.cc_brand = credit_card_data.card_type
        payment.cc_exp_month = credit_card_data.expiration_month
        payment.cc_exp_year = credit_card_data.expiration_year
        payment.save(update_fields=[
            'cc_first_digits', 'cc_last_digits', 'cc_brand',
            'cc_exp_month', 'cc_exp_year'])

    txn = create_transaction(
        payment=payment,
        kind=Transactions.AUTH,
        amount=gateway_response.pop('amount', payment.total),
        currency=gateway_response.pop('currency', payment.currency),
        gateway_response=gateway_response,
        token=getattr(result.transaction, 'id', ''),
        is_success=result.is_success)
    return txn, error


def capture(
        payment: Payment,
        amount: Decimal,
        **connection_params: Dict) -> Tuple[Transaction, str]:
    gateway = get_braintree_gateway(**connection_params)
    auth_transaction = payment.transactions.filter(
        kind=Transactions.AUTH, is_success=True).first()
    try:
        result = gateway.transaction.submit_for_settlement(
            transaction_id=auth_transaction.token, amount=str(amount))
    except braintree_sdk.exceptions.NotFoundError:
        return transaction_and_incorrect_token_error(
            payment,
            type=Transactions.CAPTURE,
            token=auth_transaction.token,
            amount=amount)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])

    txn = create_transaction(
        payment=payment,
        parent=auth_transaction,
        kind=Transactions.CAPTURE,
        amount=gateway_response.pop('amount', amount),
        currency=gateway_response.pop('currency', payment.currency),
        token=getattr(result.transaction, 'id', ''),
        is_success=result.is_success,
        gateway_response=gateway_response)
    return txn, error


def void(
        payment: Payment,
        **connection_params: Dict) -> Tuple[Transaction, str]:
    gateway = get_braintree_gateway(**connection_params)
    auth_transaction = payment.transactions.filter(
        kind=Transactions.AUTH, is_success=True).first()
    try:
        result = gateway.transaction.void(
            transaction_id=auth_transaction.token)
    except braintree_sdk.exceptions.NotFoundError:
        return transaction_and_incorrect_token_error(
            payment, type=Transactions.VOID, token=auth_transaction.token)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])
    txn = create_transaction(
        payment=payment,
        parent=auth_transaction,
        kind=Transactions.VOID,
        amount=gateway_response.pop('amount', payment.total),
        currency=gateway_response.pop('currency', payment.currency),
        gateway_response=gateway_response,
        token=getattr(result.transaction, 'id', ''),
        is_success=result.is_success)
    return txn, error


def refund(
        payment: Payment,
        amount: Decimal,
        **connection_params: Dict) -> Tuple[Transaction, str]:
    gateway = get_braintree_gateway(**connection_params)
    capture_txn = payment.transactions.filter(
        kind=Transactions.CAPTURE, is_success=True).first()
    try:
        result = gateway.transaction.refund(
            transaction_id=capture_txn.token,
            amount_or_options=str(amount))
    except braintree_sdk.exceptions.NotFoundError:
        return transaction_and_incorrect_token_error(
            payment, type=Transactions.REFUND, token=capture_txn.token,
            amount=amount)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response['errors'])
    txn = create_transaction(
        payment=payment,
        parent=capture_txn,
        kind=Transactions.REFUND,
        amount=gateway_response.pop('amount', amount),
        currency=gateway_response.pop('currency', payment.currency),
        token=getattr(result.transaction, 'id', ''),
        is_success=result.is_success,
        gateway_response=gateway_response)
    return txn, error
