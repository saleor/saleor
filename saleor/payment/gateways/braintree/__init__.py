import logging
from typing import Dict, List

import braintree as braintree_sdk
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import pgettext_lazy

from ... import TransactionKind
from ...interface import (
    CreditCardInfo,
    CustomerSource,
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    TokenConfig,
)
from .errors import DEFAULT_ERROR_MESSAGE, BraintreeException
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
    "91506": """
        Cannot refund transaction unless it is settled.
        Please try again later. Settlement time might vary depending
        on the issuers bank."""
}


def get_customer_data(payment_information: PaymentData) -> Dict:
    """Provides customer info, use only for new customer creation"""
    billing = payment_information.billing
    return {
        "order_id": payment_information.order_id,
        "billing": {
            "first_name": billing.first_name,
            "last_name": billing.last_name,
            "company": billing.company_name,
            "postal_code": billing.postal_code,
            "street_address": billing.street_address_1,
            "extended_address": billing.street_address_2,
            "locality": billing.city,
            "region": billing.country_area,
            "country_code_alpha2": billing.country,
        },
        "risk_data": {"customer_ip": payment_information.customer_ip_address or ""},
        "customer": {"email": payment_information.customer_email},
    }


def get_error_for_client(errors: List) -> str:
    """Filters all error messages and decides which one is visible for the
    client side.
    """
    if not errors:
        return ""
    default_msg = pgettext_lazy(
        "payment error", "Unable to process transaction. Please try again in a moment"
    )
    for error in errors:
        if error["code"] in ERROR_CODES_WHITELIST:
            return ERROR_CODES_WHITELIST[error["code"]] or error["message"]
    return default_msg


def extract_gateway_response(braintree_result) -> Dict:
    """Extract data from Braintree response that will be stored locally."""
    errors = []
    if not braintree_result.is_success:
        errors = [
            {"code": error.code, "message": error.message}
            for error in braintree_result.errors.deep_errors
        ]
    bt_transaction = braintree_result.transaction

    if not bt_transaction:
        return {"errors": errors}
    return {
        "transaction_id": getattr(bt_transaction, "id", ""),
        "currency": bt_transaction.currency_iso_code,
        "amount": bt_transaction.amount,  # Decimal type
        "credit_card": bt_transaction.credit_card,
        "customer_id": bt_transaction.customer_details.id,
        "errors": errors,
    }


def create_form(data, payment_information, connection_params):
    return BraintreePaymentForm(data=data, payment_information=payment_information)


def get_braintree_gateway(sandbox_mode, merchant_id, public_key, private_key):
    if not all([merchant_id, private_key, public_key]):
        raise ImproperlyConfigured("Incorrectly configured Braintree gateway.")
    environment = braintree_sdk.Environment.Sandbox
    if not sandbox_mode:
        environment = braintree_sdk.Environment.Production

    config = braintree_sdk.Configuration(
        environment=environment,
        merchant_id=merchant_id,
        public_key=public_key,
        private_key=private_key,
    )
    gateway = braintree_sdk.BraintreeGateway(config=config)
    return gateway


def get_client_token(config: GatewayConfig, token_config: TokenConfig = None) -> str:
    gateway = get_braintree_gateway(**config.connection_params)
    if not token_config:
        return gateway.client_token.generate()
    parameters = create_token_params(config, token_config)
    return gateway.client_token.generate(parameters)


def create_token_params(config: GatewayConfig, token_config: TokenConfig) -> dict:
    params = {}
    customer_id = token_config.customer_id
    if customer_id and config.store_customer:
        params["customer_id"] = customer_id
    return params


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    try:
        if not payment_information.customer_id:
            result = transaction_for_new_customer(payment_information, config)
        else:
            result = transaction_for_existing_customer(payment_information, config)
    except braintree_sdk.exceptions.NotFoundError:
        raise BraintreeException(DEFAULT_ERROR_MESSAGE)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response["errors"])
    kind = TransactionKind.CAPTURE if config.auto_capture else TransactionKind.AUTH
    return GatewayResponse(
        is_success=result.is_success,
        kind=kind,
        amount=gateway_response.get("amount", payment_information.amount),
        currency=gateway_response.get("currency", payment_information.currency),
        customer_id=gateway_response.get("customer_id"),
        transaction_id=gateway_response.get(
            "transaction_id", payment_information.token
        ),
        error=error,
        raw_response=gateway_response,
    )


def transaction_for_new_customer(
    payment_information: PaymentData, config: GatewayConfig
):
    gateway = get_braintree_gateway(**config.connection_params)
    return gateway.transaction.sale(
        {
            "amount": str(payment_information.amount),
            "payment_method_nonce": payment_information.token,
            "options": {
                "submit_for_settlement": config.auto_capture,
                "store_in_vault_on_success": payment_information.reuse_source,
                "three_d_secure": {"required": THREE_D_SECURE_REQUIRED},
            },
            **get_customer_data(payment_information),
        }
    )


def transaction_for_existing_customer(
    payment_information: PaymentData, config: GatewayConfig
):
    gateway = get_braintree_gateway(**config.connection_params)
    return gateway.transaction.sale(
        {
            "amount": str(payment_information.amount),
            "customer_id": payment_information.customer_id,
            "options": {"submit_for_settlement": config.auto_capture},
            **get_customer_data(payment_information),
        }
    )


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    gateway = get_braintree_gateway(**config.connection_params)

    try:
        result = gateway.transaction.submit_for_settlement(
            transaction_id=payment_information.token,
            amount=str(payment_information.amount),
        )
    except braintree_sdk.exceptions.NotFoundError:
        raise BraintreeException(DEFAULT_ERROR_MESSAGE)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response["errors"])

    return GatewayResponse(
        is_success=result.is_success,
        kind=TransactionKind.CAPTURE,
        amount=gateway_response.get("amount", payment_information.amount),
        currency=gateway_response.get("currency", payment_information.currency),
        transaction_id=gateway_response.get(
            "transaction_id", payment_information.token
        ),
        error=error,
        raw_response=gateway_response,
    )


def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    gateway = get_braintree_gateway(**config.connection_params)

    try:
        result = gateway.transaction.void(transaction_id=payment_information.token)
    except braintree_sdk.exceptions.NotFoundError:
        raise BraintreeException(DEFAULT_ERROR_MESSAGE)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response["errors"])

    return GatewayResponse(
        is_success=result.is_success,
        kind=TransactionKind.VOID,
        amount=gateway_response.get("amount", payment_information.amount),
        currency=gateway_response.get("currency", payment_information.currency),
        transaction_id=gateway_response.get(
            "transaction_id", payment_information.token
        ),
        error=error,
        raw_response=gateway_response,
    )


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    gateway = get_braintree_gateway(**config.connection_params)

    try:
        result = gateway.transaction.refund(
            transaction_id=payment_information.token,
            amount_or_options=str(payment_information.amount),
        )
    except braintree_sdk.exceptions.NotFoundError:
        raise BraintreeException(DEFAULT_ERROR_MESSAGE)

    gateway_response = extract_gateway_response(result)
    error = get_error_for_client(gateway_response["errors"])

    return GatewayResponse(
        is_success=result.is_success,
        kind=TransactionKind.REFUND,
        amount=gateway_response.get("amount", payment_information.amount),
        currency=gateway_response.get("currency", payment_information.currency),
        transaction_id=gateway_response.get(
            "transaction_id", payment_information.token
        ),
        error=error,
        raw_response=gateway_response,
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    auth_resp = authorize(payment_information, config)
    return auth_resp


def list_client_sources(
    config: GatewayConfig, customer_id: str
) -> List[CustomerSource]:
    gateway = get_braintree_gateway(**config.connection_params)
    customer = gateway.customer.find(customer_id)
    if not customer:
        return []
    return [
        extract_credit_card_data(card, "braintree") for card in customer.credit_cards
    ]


def extract_credit_card_data(card, gateway_name):
    credit_card = CreditCardInfo(
        exp_year=int(card.expiration_year),
        exp_month=int(card.expiration_month),
        last_4=card.last_4,
        name_on_card=card.cardholder_name,
    )
    return CustomerSource(
        id=card.unique_number_identifier,
        gateway=gateway_name,
        credit_card_info=credit_card,
    )
