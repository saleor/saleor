import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, List, Optional

import requests
from posuto import Posuto
from requests.auth import HTTPBasicAuth

from ... import PaymentError
from ...interface import AddressData, PaymentData, RefundLineData
from ...utils import price_to_minor_unit
from .const import NP_ATOBARAI, NP_TEST_URL, NP_URL, REQUEST_TIMEOUT
from .utils import np_atobarai_opentracing_trace

if TYPE_CHECKING:
    from . import ApiConfig


logger = logging.getLogger(__name__)


def get_url(config: "ApiConfig", path: str = "") -> str:
    """Resolve test/production URLs based on the api config."""
    return f"{NP_TEST_URL if config.test_mode else NP_URL}{path}"


def _request(
    config: "ApiConfig",
    method: str,
    path: str = "",
    json: Optional[dict] = None,
) -> requests.Response:
    with np_atobarai_opentracing_trace("np-atobarai.utilities.request"):
        response = requests.request(
            method=method,
            url=get_url(config, path),
            timeout=REQUEST_TIMEOUT,
            json=json or {},
            auth=HTTPBasicAuth(config.merchant_code, config.sp_code),
            headers={"X-NP-Terminal-Id": config.terminal_id},
        )
        if 400 < response.status_code <= 600:
            raise requests.HTTPError
        return response


def np_request(
    config: "ApiConfig", method: str, path: str = "", json: Optional[dict] = None
) -> requests.Response:
    try:
        return _request(config, method, path, json)
    except requests.RequestException:
        msg = "Cannot connect to NP Atobarai."
        logger.warning(msg, exc_info=True)
        raise PaymentError(msg)


def handle_unrecoverable_state(
    action: str,
    transaction_id: str,
    error_codes: Iterable[str],
) -> None:
    logger.error(
        "Payment #%s %s Unrecoverable Error: %s",
        transaction_id,
        action,
        ", ".join(error_codes),
    )


def get_errors(response_data: dict) -> Iterable[str]:
    if "errors" not in response_data:
        return []
    return set(response_data["errors"][0]["codes"])


def health_check(config: "ApiConfig") -> bool:
    try:
        _request(config, "post", "/authorizations/find")
        return True
    except requests.RequestException:
        return False


def format_name(ad: AddressData):
    """Follow the Japanese name guidelines."""
    return f"{ad.first_name} {ad.last_name}".strip()


def format_address(config: "ApiConfig", ad: AddressData):
    """Follow the Japanese address guidelines."""
    # example: "東京都千代田区麹町４－２－６　住友不動産麹町ファーストビル５階"
    if not config.fill_missing_address:
        return f"{ad.country_area}{ad.street_address_2}{ad.street_address_1}"
    with Posuto() as pp:
        try:
            jap_ad = pp.get(ad.postal_code)
        except KeyError:
            raise PaymentError(
                "Valid Japanese address is required for transaction in NP Atobarai."
            )
        else:
            return (
                f"{ad.country_area}"
                f"{jap_ad.city}"
                f"{jap_ad.neighborhood}"
                f"{ad.street_address_2}"
                f"{ad.street_address_1}"
            )


def format_price(price: Decimal, currency: str) -> int:
    return int(price_to_minor_unit(price, currency))


def get_refunded_goods(
    refund_lines: List[RefundLineData],
    payment_information: PaymentData,
) -> List[dict]:
    refund_lines_dict = {
        line.product_sku: line.quantity for line in refund_lines if line.product_sku
    }

    goods = []

    for payment_line in payment_information.lines:
        quantity = refund_lines_dict.get(
            payment_line.product_sku, payment_line.quantity
        )
        if quantity:
            goods.append(
                {
                    "goods_name": payment_line.product_name,
                    "goods_price": format_price(
                        payment_line.gross, payment_information.currency
                    ),
                    "quantity": quantity,
                }
            )
    return goods


def get_goods(payment_information: PaymentData) -> List[dict]:
    return [
        {
            "quantity": line.quantity,
            "goods_name": line.product_name,
            "goods_price": format_price(line.gross, payment_information.currency),
        }
        for line in payment_information.lines
    ]


def get_discount(
    payment_information: PaymentData,
) -> List[dict]:
    product_lines = get_goods(payment_information)
    return product_lines + [
        {
            "goods_name": "Discount",
            "goods_price": format_price(
                -payment_information.amount,
                payment_information.currency,
            ),
            "quantity": 1,
        }
    ]


def cancel(config: "ApiConfig", transaction_id: str) -> dict:
    data = {"transactions": [{"np_transaction_id": transaction_id}]}
    response = np_request(config, "patch", "/transactions/cancel", json=data)
    return response.json()


def register(
    config: "ApiConfig",
    payment_information: "PaymentData",
    billed_amount: Optional[int] = None,
    goods: Optional[List[dict]] = None,
) -> dict:
    if billed_amount is None:
        billed_amount = format_price(
            payment_information.amount, payment_information.currency
        )
    if goods is None:
        goods = get_goods(payment_information)

    payment_information.refresh_order_date()

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
                "shop_order_date": payment_information.order_date,
                "settlement_type": NP_ATOBARAI,
                "billed_amount": billed_amount,
                "customer": {
                    "customer_name": billing.first_name,
                    "company_name": billing.company_name,
                    "zip_code": billing.postal_code,
                    "address": format_address(config, billing),
                    "tel": billing.phone.replace("+81", "0"),
                    "email": payment_information.customer_email,
                },
                "dest_customer": {
                    "customer_name": format_name(shipping),
                    "company_name": shipping.company_name,
                    "zip_code": shipping.postal_code,
                    "address": format_address(config, shipping),
                    "tel": shipping.phone.replace("+81", "0"),
                },
                "goods": goods,
            },
        ]
    }

    return np_request(config, "post", "/transactions", json=data).json()
