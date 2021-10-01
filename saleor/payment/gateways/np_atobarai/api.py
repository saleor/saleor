from typing import Optional

import requests
from requests.auth import HTTPBasicAuth

from saleor.payment import PaymentError
from saleor.payment.gateways.np_atobarai.api_types import (
    ApiConfig,
    PaymentResult,
    PaymentStatus,
)
from saleor.payment.gateways.np_atobarai.errors import (
    UNKNOWN_ERROR,
    TransactionCancellationResultError,
)
from saleor.payment.interface import PaymentData
from saleor.payment.models import Payment

REQUEST_TIMEOUT = 15


def get_url(config: ApiConfig, path: str = "") -> str:
    """Resolve test/production URLs based on the api config."""
    if config.test_mode:
        return f"https://ctcp.np-payment-gateway.com/v1{path}"
    return f"https://cp.np-payment-gateway.com/v1{path}"


def np_request(
    config: ApiConfig, method: str, path: str = "", json: Optional[dict] = None
) -> requests.Response:
    try:
        return requests.request(
            method=method,
            url=get_url(config, path),
            timeout=REQUEST_TIMEOUT,
            json=json or {},
            auth=HTTPBasicAuth(config.merchant_code, config.sp_code),
            headers={"X-NP-Terminal-Id": config.terminal_id},
        )
    except requests.RequestException:
        raise PaymentError("Cannot connect to NP Atobarai.")


def health_check(config: ApiConfig) -> bool:
    try:
        response = np_request(config, "post", "/authorizations/find")
        return response.status_code not in [401, 403]
    except PaymentError:
        return False


def cancel_transaction(
    config: ApiConfig, payment_information: PaymentData
) -> PaymentResult:
    # todo: optimize
    psp_reference = Payment.objects.get(id=payment_information.payment_id).psp_reference

    if not psp_reference:
        raise PaymentError("Payment cannot be voided.")

    data = {"transactions": [{"np_transaction_id": psp_reference}]}

    response = np_request(config, "post", "/transactions", json=data)
    response_data = response.json()

    if "errors" in response_data:
        error_codes = set(response_data["errors"][0]["codes"])

        error_messages = []
        for error_code in error_codes:
            try:
                message = TransactionCancellationResultError[error_code].value
            except KeyError:
                message = f"#{error_code}: {UNKNOWN_ERROR}"

            error_messages.append(message)

        return PaymentResult(
            status=PaymentStatus.FAILED,
            psp_reference=psp_reference,
            errors=error_messages,
        )
    else:
        return PaymentResult(
            status=PaymentStatus.SUCCESS,
            psp_reference=psp_reference,
        )
