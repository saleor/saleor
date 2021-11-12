import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional

import requests
from django.utils import timezone
from posuto import Posuto
from requests.auth import HTTPBasicAuth

from ...interface import AddressData, PaymentData
from ...utils import price_to_minor_unit
from .api_types import NPResponse, error_np_response
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
) -> NPResponse:
    try:
        response = _request(config, method, path, json)
        response_data = response.json()
        if "errors" in response_data:
            return NPResponse({}, response_data["errors"][0]["codes"])
        return NPResponse(response_data["results"][0], [])
    except requests.RequestException:
        msg = "Cannot connect to NP Atobarai."
        logger.warning(msg, exc_info=True)
        return NPResponse({}, [msg])


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


def health_check(config: "ApiConfig") -> bool:
    try:
        _request(config, "post", "/authorizations/find")
        return True
    except requests.RequestException:
        return False


def format_name(ad: AddressData) -> str:
    """Follow the Japanese name guidelines."""
    return f"{ad.last_name}　{ad.first_name}".strip()


def format_address(config: "ApiConfig", ad: AddressData) -> Optional[str]:
    """Follow the Japanese address guidelines."""
    # example: "東京都千代田区麹町４－２－６　住友不動産麹町ファーストビル５階"
    if not config.fill_missing_address:
        return f"{ad.country_area}{ad.street_address_1}{ad.street_address_2}"
    with Posuto() as pp:
        try:
            jap_ad = pp.get(ad.postal_code)
        except KeyError:
            return None
        else:
            return (
                f"{ad.country_area}"
                f"{jap_ad.city}"
                f"{jap_ad.neighborhood}"
                f"{ad.street_address_1}"
                f"{ad.street_address_2}"
            )


def format_price(price: Decimal, currency: str) -> int:
    return int(price_to_minor_unit(price, currency))


def get_refunded_goods(
    config: "ApiConfig",
    refund_data: Dict[int, int],
    payment_information: PaymentData,
) -> List[dict]:
    return [
        {
            "goods_name": line.product_sku if config.sku_as_name else line.product_name,
            "goods_price": format_price(line.gross, payment_information.currency),
            "quantity": quantity,
        }
        for line in payment_information.lines
        if (quantity := refund_data.get(line.variant_id, line.quantity))
    ]


def get_goods(config: "ApiConfig", payment_information: PaymentData) -> List[dict]:
    return [
        {
            "quantity": line.quantity,
            "goods_name": line.product_sku if config.sku_as_name else line.product_name,
            "goods_price": format_price(line.gross, payment_information.currency),
        }
        for line in payment_information.lines
    ]


def get_goods_with_discount(
    config: "ApiConfig",
    payment_information: PaymentData,
) -> List[dict]:
    product_lines = get_goods(config, payment_information)
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


def cancel(config: "ApiConfig", transaction_id: str) -> NPResponse:
    data = {"transactions": [{"np_transaction_id": transaction_id}]}
    return np_request(config, "patch", "/transactions/cancel", json=data)


def register(
    config: "ApiConfig",
    payment_information: "PaymentData",
    billed_amount: Optional[int] = None,
    goods: Optional[List[dict]] = None,
) -> NPResponse:
    if billed_amount is None:
        billed_amount = format_price(
            payment_information.amount, payment_information.currency
        )
    if goods is None:
        goods = get_goods(config, payment_information)

    order_date = timezone.now().strftime("%Y-%m-%d")

    billing = payment_information.billing
    shipping = payment_information.shipping

    if not billing:
        return error_np_response(
            "Billing address is required for transaction in NP Atobarai."
        )
    if not shipping:
        return error_np_response(
            "Shipping address is required for transaction in NP Atobarai."
        )

    formatted_billing = format_address(config, billing)
    formatted_shipping = format_address(config, shipping)

    if not formatted_billing:
        return error_np_response("Billing address is not a valid Japanese address.")
    if not formatted_shipping:
        return error_np_response("Shipping address is not a valid Japanese address.")

    data = {
        "transactions": [
            {
                "shop_transaction_id": payment_information.payment_id,
                "shop_order_date": order_date,
                "settlement_type": NP_ATOBARAI,
                "billed_amount": billed_amount,
                "customer": {
                    "customer_name": billing.first_name,
                    "company_name": billing.company_name,
                    "zip_code": billing.postal_code,
                    "address": formatted_billing,
                    "tel": billing.phone.replace("+81", "0"),
                    "email": payment_information.customer_email,
                },
                "dest_customer": {
                    "customer_name": format_name(shipping),
                    "company_name": shipping.company_name,
                    "zip_code": shipping.postal_code,
                    "address": formatted_shipping,
                    "tel": shipping.phone.replace("+81", "0"),
                },
                "goods": goods,
            },
        ]
    }

    return np_request(config, "post", "/transactions", json=data)


def report(
    config: "ApiConfig",
    psp_reference: Optional[str],
    shipping_slip_number: Optional[str],
) -> NPResponse:
    shipping_company_code = config.shipping_company

    if not psp_reference:
        return error_np_response("Payment does not have psp reference.")

    if not shipping_slip_number:
        return error_np_response("Fulfillment does not have tracking number.")

    data = {
        "transactions": [
            {
                "np_transaction_id": psp_reference,
                "pd_company_code": shipping_company_code,
                "slip_no": shipping_slip_number,
            }
        ]
    }

    return np_request(config, "post", "/shipments", json=data)
