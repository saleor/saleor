from typing import Optional

import requests
from django.utils import timezone
from requests.auth import HTTPBasicAuth

from ...interface import AddressData, PaymentData
from ...utils import price_to_minor_unit
from .api_types import ApiConfig, PaymentResult, PaymentStatus
from .const import NP_ATOBARAI
from .errors import UNKNOWN_ERROR, TransactionRegistrationResultError

REQUEST_TIMEOUT = 15


def get_url(config: ApiConfig, path: str = "") -> str:
    """Resolve test/production URLs based on the api config."""
    if config.test_mode:
        return f"https://ctcp.np-payment-gateway.com/v1{path}"
    return f"https://cp.np-payment-gateway.com/v1{path}"


def _request(
    config: ApiConfig, method: str, path: str = "", json: Optional[dict] = None
) -> requests.Response:
    return requests.request(
        method=method,
        url=get_url(config, path),
        timeout=REQUEST_TIMEOUT,
        json=json or {},
        auth=HTTPBasicAuth(config.merchant_code, config.sp_code),
        headers={"X-NP-Terminal-Id": config.terminal_id},
    )


def health_check(config: ApiConfig) -> bool:
    response = _request(config, "post", "/authorizations/find")
    return response.status_code not in [401, 403]


def _format_name(ad: AddressData):
    """Follow the japanese name guidelines."""
    return f"{ad.first_name} {ad.last_name}".lstrip().rstrip()


# TODO: theoretically it should work, but city info is blank
def _format_address(ad: AddressData):
    """Follow the japanese address guidelines."""
    # return "東京都千代田区麹町４－２－６　住友不動産麹町ファーストビル５階"
    return f"{ad.country_area}{ad.city}{ad.city_area}{ad.street_address_1}"


def register_transaction(
    config: ApiConfig, payment_information: "PaymentData"
) -> PaymentResult:
    order_date = timezone.now().strftime("%Y-%m-%d")
    assert payment_information.billing
    assert payment_information.shipping
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
                    "customer_name": payment_information.billing.first_name,
                    "company_name": payment_information.billing.company_name,
                    "zip_code": payment_information.billing.postal_code,
                    "address": _format_address(payment_information.billing),
                    "tel": payment_information.billing.phone.replace("+81", "0"),
                    "email": payment_information.customer_email,
                },
                "dest_customer": {
                    "customer_name": _format_name(payment_information.shipping),
                    "company_name": payment_information.shipping.company_name,
                    "zip_code": payment_information.shipping.postal_code,
                    "address": _format_address(payment_information.shipping),
                    "tel": payment_information.shipping.phone.replace("+81", "0"),
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

    response = _request(config, "post", "/transactions", json=data)
    response_data = response.json()
    print(response_data)

    if "results" in response_data:
        transaction = response_data["results"][0]
        return PaymentResult(
            status=transaction["authori_result"],
            psp_reference=transaction["np_transaction_id"],
        )

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
