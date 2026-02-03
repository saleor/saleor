"""HyperPay API communication layer."""

import logging
import re
from decimal import Decimal
from typing import Any

import requests

from .consts import (
    BACKOFFICE_PATH,
    CHECKOUT_PATH,
    PAYMENT_STATUS_PATH,
    PAYMENT_TYPE_CAPTURE,
    PAYMENT_TYPE_DEBIT,
    PAYMENT_TYPE_PREAUTH,
    PAYMENT_TYPE_REFUND,
    PAYMENT_TYPE_REVERSAL,
    PRODUCTION_API_URL,
    SUCCESS_CODES_PATTERN,
    TEST_API_URL,
)

logger = logging.getLogger(__name__)

# Request timeout in seconds
REQUEST_TIMEOUT = 30


def get_api_url(test_mode: bool) -> str:
    """Get the appropriate API URL based on mode."""
    return TEST_API_URL if test_mode else PRODUCTION_API_URL


def is_successful_result(result_code: str) -> bool:
    """Check if the result code indicates a successful transaction."""
    return bool(re.match(SUCCESS_CODES_PATTERN, result_code))


def prepare_checkout(
    entity_id: str,
    access_token: str,
    amount: Decimal,
    currency: str,
    payment_type: str,
    payment_brands: str,
    merchant_transaction_id: str,
    test_mode: bool = True,
    customer_email: str | None = None,
    billing_address: dict | None = None,
    shipping_address: dict | None = None,
) -> dict[str, Any]:
    """
    Create a checkout session with HyperPay.

    This generates a checkout ID that can be used with the payment widget
    or for server-to-server transactions.

    Args:
        entity_id: HyperPay Entity ID
        access_token: HyperPay Access Token
        amount: Payment amount
        currency: Currency code (e.g., 'SAR', 'AED')
        payment_type: Payment type (DB=Debit, PA=Pre-auth)
        payment_brands: Space-separated payment brands (e.g., 'VISA MASTER MADA')
        merchant_transaction_id: Your unique transaction reference
        test_mode: Whether to use test environment
        customer_email: Customer email address
        billing_address: Billing address dict
        shipping_address: Shipping address dict

    Returns:
        dict with 'checkout_id' on success, or 'error' on failure
    """
    api_url = get_api_url(test_mode)
    endpoint = f"{api_url}{CHECKOUT_PATH}"

    # Format amount to 2 decimal places
    formatted_amount = f"{amount:.2f}"

    data = {
        "entityId": entity_id,
        "amount": formatted_amount,
        "currency": currency,
        "paymentType": payment_type,
        "merchantTransactionId": merchant_transaction_id,
    }

    if payment_brands:
        data["paymentBrand"] = payment_brands

    if customer_email:
        data["customer.email"] = customer_email

    # Add billing address if provided
    if billing_address:
        address_mapping = {
            "street1": "billing.street1",
            "city": "billing.city",
            "state": "billing.state",
            "postcode": "billing.postcode",
            "country": "billing.country",
        }
        for key, param in address_mapping.items():
            if billing_address.get(key):
                data[param] = billing_address[key]

    # Add shipping address if provided
    if shipping_address:
        address_mapping = {
            "street1": "shipping.street1",
            "city": "shipping.city",
            "state": "shipping.state",
            "postcode": "shipping.postcode",
            "country": "shipping.country",
        }
        for key, param in address_mapping.items():
            if shipping_address.get(key):
                data[param] = shipping_address[key]

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.post(
            endpoint,
            data=data,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response_data = response.json()

        result_code = response_data.get("result", {}).get("code", "")
        result_description = response_data.get("result", {}).get("description", "")

        if is_successful_result(result_code):
            return {
                "checkout_id": response_data.get("id"),
                "result_code": result_code,
                "result_description": result_description,
            }
        else:
            logger.error(
                "HyperPay checkout creation failed: %s - %s",
                result_code,
                result_description,
            )
            return {
                "error": result_description or "Failed to create checkout",
                "result_code": result_code,
            }

    except requests.exceptions.RequestException as e:
        logger.exception("HyperPay API request failed")
        return {"error": str(e)}


def get_payment_status(
    checkout_id: str,
    entity_id: str,
    access_token: str,
    test_mode: bool = True,
) -> dict[str, Any]:
    """
    Get the payment status for a checkout.

    Args:
        checkout_id: The checkout ID from prepare_checkout
        entity_id: HyperPay Entity ID
        access_token: HyperPay Access Token
        test_mode: Whether to use test environment

    Returns:
        dict with payment status information
    """
    api_url = get_api_url(test_mode)
    endpoint = f"{api_url}{PAYMENT_STATUS_PATH.format(checkout_id=checkout_id)}"

    params = {"entityId": entity_id}
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(
            endpoint,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response_data = response.json()

        result_code = response_data.get("result", {}).get("code", "")
        result_description = response_data.get("result", {}).get("description", "")

        return {
            "success": is_successful_result(result_code),
            "result_code": result_code,
            "result_description": result_description,
            "payment_id": response_data.get("id"),
            "payment_type": response_data.get("paymentType"),
            "amount": response_data.get("amount"),
            "currency": response_data.get("currency"),
            "payment_brand": response_data.get("paymentBrand"),
            "merchant_transaction_id": response_data.get("merchantTransactionId"),
            "raw_response": response_data,
        }

    except requests.exceptions.RequestException as e:
        logger.exception("HyperPay payment status request failed")
        return {"success": False, "error": str(e)}


def capture_payment(
    payment_id: str,
    entity_id: str,
    access_token: str,
    amount: Decimal,
    currency: str,
    test_mode: bool = True,
) -> dict[str, Any]:
    """
    Capture a pre-authorized payment.

    Args:
        payment_id: The payment ID from the original authorization
        entity_id: HyperPay Entity ID
        access_token: HyperPay Access Token
        amount: Amount to capture
        currency: Currency code
        test_mode: Whether to use test environment

    Returns:
        dict with capture result
    """
    api_url = get_api_url(test_mode)
    endpoint = f"{api_url}{BACKOFFICE_PATH}/{payment_id}"

    formatted_amount = f"{amount:.2f}"

    data = {
        "entityId": entity_id,
        "amount": formatted_amount,
        "currency": currency,
        "paymentType": PAYMENT_TYPE_CAPTURE,
    }

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.post(
            endpoint,
            data=data,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response_data = response.json()

        result_code = response_data.get("result", {}).get("code", "")
        result_description = response_data.get("result", {}).get("description", "")

        return {
            "success": is_successful_result(result_code),
            "result_code": result_code,
            "result_description": result_description,
            "transaction_id": response_data.get("id"),
            "raw_response": response_data,
        }

    except requests.exceptions.RequestException as e:
        logger.exception("HyperPay capture request failed")
        return {"success": False, "error": str(e)}


def refund_payment(
    payment_id: str,
    entity_id: str,
    access_token: str,
    amount: Decimal,
    currency: str,
    test_mode: bool = True,
) -> dict[str, Any]:
    """
    Refund a payment.

    Args:
        payment_id: The payment ID to refund
        entity_id: HyperPay Entity ID
        access_token: HyperPay Access Token
        amount: Amount to refund
        currency: Currency code
        test_mode: Whether to use test environment

    Returns:
        dict with refund result
    """
    api_url = get_api_url(test_mode)
    endpoint = f"{api_url}{BACKOFFICE_PATH}/{payment_id}"

    formatted_amount = f"{amount:.2f}"

    data = {
        "entityId": entity_id,
        "amount": formatted_amount,
        "currency": currency,
        "paymentType": PAYMENT_TYPE_REFUND,
    }

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.post(
            endpoint,
            data=data,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response_data = response.json()

        result_code = response_data.get("result", {}).get("code", "")
        result_description = response_data.get("result", {}).get("description", "")

        return {
            "success": is_successful_result(result_code),
            "result_code": result_code,
            "result_description": result_description,
            "transaction_id": response_data.get("id"),
            "raw_response": response_data,
        }

    except requests.exceptions.RequestException as e:
        logger.exception("HyperPay refund request failed")
        return {"success": False, "error": str(e)}


def void_payment(
    payment_id: str,
    entity_id: str,
    access_token: str,
    test_mode: bool = True,
) -> dict[str, Any]:
    """
    Void/reverse a payment.

    Args:
        payment_id: The payment ID to void
        entity_id: HyperPay Entity ID
        access_token: HyperPay Access Token
        test_mode: Whether to use test environment

    Returns:
        dict with void result
    """
    api_url = get_api_url(test_mode)
    endpoint = f"{api_url}{BACKOFFICE_PATH}/{payment_id}"

    data = {
        "entityId": entity_id,
        "paymentType": PAYMENT_TYPE_REVERSAL,
    }

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.post(
            endpoint,
            data=data,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response_data = response.json()

        result_code = response_data.get("result", {}).get("code", "")
        result_description = response_data.get("result", {}).get("description", "")

        return {
            "success": is_successful_result(result_code),
            "result_code": result_code,
            "result_description": result_description,
            "transaction_id": response_data.get("id"),
            "raw_response": response_data,
        }

    except requests.exceptions.RequestException as e:
        logger.exception("HyperPay void request failed")
        return {"success": False, "error": str(e)}
