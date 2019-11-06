from typing import Dict, List, Optional

import json

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from decimal import Decimal

from ... import TransactionKind
from ...interface import (
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    TokenConfig,
)
from .utils import ClientTokenProvider, PayuSession

from ....order.models import Order


def get_client_token(
    config: GatewayConfig, token_config: Optional[TokenConfig] = None
) -> str:
    client_id = config.connection_params["client_id"]
    client_secret_key = config.connection_params["client_secret_key"]
    sandbox_mode = config.connection_params["sandbox_mode"]

    client_token_provider = ClientTokenProvider(
        client_id=client_id,
        client_secret_key=client_secret_key,
        sandbox_mode=sandbox_mode
    )

    return client_token_provider.get_client_token()


def get_payu_gateway(client_id, client_secret_key, merchant_pos_id, sandbox_mode):
    if not all([client_id, client_secret_key, merchant_pos_id]):
        raise ImproperlyConfigured("Incorrectly configured PayU gateway.")

    client_token_provider = ClientTokenProvider(
        client_id=client_id,
        client_secret_key=client_secret_key,
        sandbox_mode=sandbox_mode
    )

    gateway = PayuSession(client_token_provider=client_token_provider)
    return gateway


def authorize(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    # Handle connecting to the gateway and sending the charge request here
    gateway = get_payu_gateway(**config.connection_params)
    merchant_pos_id = config.connection_params["merchant_pos_id"]
    validity_time = config.connection_params["validity_time"]
    sandbox_mode = config.connection_params["sandbox_mode"]
    continue_url = config.connection_params["continue_url"]
    payu_notify_url = config.connection_params["payu_notification_url"]
    payu_notify_url = payu_notify_url + reverse(
        'order:payu-notification', kwargs={"token": payment_information.token})

    if sandbox_mode:
        order_url = "https://secure.snd.payu.com/api/v2_1/orders/"
    else:
        order_url = "https://secure.payu.com/api/v2_1/orders/"

    total_amount = str(int(payment_information.amount * Decimal("100")))

    products = []

    order = Order.objects.get(id=payment_information.order_id)
    order_lines = order.lines.all()

    for order_line in order_lines:
        products.append({
            "name": order_line.product_name,
            "unitPrice": str(int(order_line.unit_price.gross.amount * 100)),
            "quantity": str(order_line.quantity)
        })

    payload = {
        "extOrderId": order.pk,
        "notifyUrl": payu_notify_url,
        "continueUrl": continue_url,
        "customerIp": payment_information.customer_ip_address,
        'merchantPosId': merchant_pos_id,
        "validityTime": validity_time,
        "description": "Order #" + str(payment_information.order_id),
        "currencyCode": payment_information.currency,
        "totalAmount": total_amount,
        "products": products,
    }

    jsondata = json.dumps(payload)
    headers = {'Content-Type': 'application/json'}

    with gateway:
        response = gateway.post(order_url, data=jsondata, headers=headers,
                                allow_redirects=False)
        gateway_response = response.json()
        is_success = False
        error_description = None
        if (
                response.status_code == 302
                and gateway_response["status"]["statusCode"] == "SUCCESS"
        ):
            is_success = True
        else:
            try:
                error_description = gateway_response["status"]["statusDesc"]
            except KeyError:
                pass

        return GatewayResponse(
            is_success=is_success,
            action_required=True,
            kind=TransactionKind.AUTH,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=gateway_response.get(
                "orderId", payment_information.token
            ),
            customer_id=payment_information.customer_id,
            raw_response=gateway_response,
            error=error_description,
        )


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    transaction_id = payment_information.token
    gateway = get_payu_gateway(**config.connection_params)
    sandbox_mode = config.connection_params["sandbox_mode"]
    headers = {'Content-Type': 'application/json'}

    if sandbox_mode:
        order_url = f"https://secure.snd.payu.com/api/v2_1/orders/{transaction_id}"
    else:
        order_url = f"https://secure.payu.com/api/v2_1/orders/{transaction_id}"

    with gateway:
        response = gateway.post(order_url, headers=headers)
        gateway_response = response.json()

    is_success = False
    error_description = None

    if gateway_response["status"]["statusCode"] == "SUCCESS":
            if gateway_response["orders"][0]["status"] == "CAPTURED":
                is_success = True
    else:
        error_description = gateway_response["status"]["statusDesc"]

    # not sure about transaction_id, it's duplicated in mutltiple transaction objects
    return GatewayResponse(
        is_success=is_success,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=Decimal(gateway_response["orders"][0]["status"]["total_amount"]) / 100,
        currency=payment_information.currency,
        transaction_id=gateway_response.get(
            "orderId", payment_information.token
        ),
        raw_response=gateway_response,
        error=error_description,
    )


# def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
#     gateway = get_braintree_gateway(**config.connection_params)
#
#     try:
#         result = gateway.transaction.void(transaction_id=payment_information.token)
#     except braintree_sdk.exceptions.NotFoundError:
#         raise BraintreeException(DEFAULT_ERROR_MESSAGE)
#
#     gateway_response = extract_gateway_response(result)
#     error = get_error_for_client(gateway_response["errors"])
#
#     return GatewayResponse(
#         is_success=result.is_success,
#         action_required=False,
#         kind=TransactionKind.VOID,
#         amount=gateway_response.get("amount", payment_information.amount),
#         currency=gateway_response.get("currency", payment_information.currency),
#         transaction_id=gateway_response.get(
#             "transaction_id", payment_information.token
#         ),
#         error=error,
#         raw_response=gateway_response,
#     )


# def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
#     gateway = get_braintree_gateway(**config.connection_params)
#
#     try:
#         result = gateway.transaction.refund(
#             transaction_id=payment_information.token,
#             amount_or_options=str(payment_information.amount),
#         )
#     except braintree_sdk.exceptions.NotFoundError:
#         raise BraintreeException(DEFAULT_ERROR_MESSAGE)
#
#     gateway_response = extract_gateway_response(result)
#     error = get_error_for_client(gateway_response["errors"])
#
#     return GatewayResponse(
#         is_success=result.is_success,
#         action_required=False,
#         kind=TransactionKind.REFUND,
#         amount=gateway_response.get("amount", payment_information.amount),
#         currency=gateway_response.get("currency", payment_information.currency),
#         transaction_id=gateway_response.get(
#             "transaction_id", payment_information.token
#         ),
#         error=error,
#         raw_response=gateway_response,
#     )


def process_payment(
        payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    auth_resp = authorize(payment_information, config)
    return auth_resp
