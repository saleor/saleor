from typing import Optional

import posuto
import requests
from django.utils import timezone
from requests.auth import HTTPBasicAuth

from saleor.payment import PaymentError

from ...interface import AddressData, PaymentData
from ...utils import price_to_minor_unit
from .api_types import ApiConfig, PaymentResult, PaymentStatus
from .const import NP_ATOBARAI, NP_TEST_URL, NP_URL
from .errors import (
    UNKNOWN_ERROR,
    TransactionRegistrationResultError,
    get_reason_messages_from_codes,
)

REQUEST_TIMEOUT = 15


def get_url(config: ApiConfig, path: str = "") -> str:
    """Resolve test/production URLs based on the api config."""
    return f"{(NP_TEST_URL if config.test_mode else NP_URL)}{path}"


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


def _format_name(ad: AddressData):
    """Follow the japanese name guidelines."""
    return f"{ad.first_name} {ad.last_name}".lstrip().rstrip()


def _format_address(ad: AddressData):
    """Follow the japanese address guidelines."""
    # example: "東京都千代田区麹町４－２－６　住友不動産麹町ファーストビル５階"
    jap_ad = posuto.get(ad.postal_code)
    return (
        f"{ad.country_area}"
        f"{jap_ad.city}"
        f"{jap_ad.neighborhood}"
        f"{ad.street_address_2}"
        f"{ad.street_address_1}"
    )


def register_transaction(
    config: ApiConfig, payment_information: "PaymentData"
) -> PaymentResult:
    order_date = timezone.now().strftime("%Y-%m-%d")

    billing = payment_information.billing
    shipping = payment_information.shipping

    if not billing:
        raise PaymentError(
            "Billing address is required for transaction in NP Atobarai."
        )
    if not shipping:
        raise PaymentError(
            "Shipping address is required for transaction in NP Atobarai."
        )

    data = {
        "transactions": [
            {
                "shop_transaction_id": payment_information.payment_id,
                "shop_order_date": order_date,
                "settlement_type": NP_ATOBARAI,
                "billed_amount": int(
                    price_to_minor_unit(
                        payment_information.amount, payment_information.currency
                    )
                ),
                "customer": {
                    "customer_name": billing.first_name,
                    "company_name": billing.company_name,
                    "zip_code": billing.postal_code,
                    "address": _format_address(billing),
                    "tel": billing.phone.replace("+81", "0"),
                    "email": payment_information.customer_email,
                },
                "dest_customer": {
                    "customer_name": _format_name(shipping),
                    "company_name": shipping.company_name,
                    "zip_code": shipping.postal_code,
                    "address": _format_address(shipping),
                    "tel": shipping.phone.replace("+81", "0"),
                },
                "goods": [
                    {
                        "quantity": line.quantity,
                        "goods_name": line.description,
                        "goods_price": int(
                            price_to_minor_unit(
                                line.gross, payment_information.currency
                            )
                        ),
                    }
                    for line in payment_information.lines
                ],
            },
        ]
    }

    response = np_request(config, "post", "/transactions", json=data)
    response_data = response.json()

    if "results" in response_data:
        transaction = response_data["results"][0]
        status = transaction["authori_result"]
        transaction_id = transaction["np_transaction_id"]
        errors = []

        if status == PaymentStatus.PENDING:
            cancel_transaction(config, transaction_id)
            errors = get_reason_messages_from_codes(set(response_data["authori_hold"]))

        return PaymentResult(status=status, psp_reference=transaction_id, errors=errors)

    if "errors" in response_data:
        error_codes = set(response_data["errors"][0]["codes"])

        # TODO: processing unknown errors !!!
        error_messages = []
        for error_code in error_codes:
            try:
                message = TransactionRegistrationResultError[error_code].value
            except KeyError:
                message = f"#{error_code}: {UNKNOWN_ERROR}"

            error_messages.append(message)
    else:
        error_messages = [UNKNOWN_ERROR]

    return PaymentResult(status=PaymentStatus.FAILED, errors=error_messages)


def cancel_transaction(config: ApiConfig, transaction_id: str) -> None:
    data = {"transactions": [{"np_transaction_id": transaction_id}]}

    # TODO: how to do error handling here?
    #   * passing errors to GatewayResponse
    #   * logging
    np_request(config, "post", "/transactions/cancel", json=data)
