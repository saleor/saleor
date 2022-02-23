import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

import requests
from django.utils import timezone
from posuto import Posuto
from requests.auth import HTTPBasicAuth

from ....order.models import Order
from ... import PaymentError
from ...interface import AddressData, PaymentData, PaymentLineData, RefundData
from ...models import Payment
from ...utils import price_to_minor_unit
from .api_types import NPResponse, error_np_response
from .const import NP_ATOBARAI, REQUEST_TIMEOUT
from .errors import (
    BILLING_ADDRESS_INVALID,
    NO_BILLING_ADDRESS,
    NO_PSP_REFERENCE,
    NO_SHIPPING_ADDRESS,
    NO_TRACKING_NUMBER,
    NP_CONNECTION_ERROR,
    SHIPPING_ADDRESS_INVALID,
    SHIPPING_COMPANY_CODE_INVALID,
)
from .utils import (
    create_refunded_lines,
    notify_dashboard,
    np_atobarai_opentracing_trace,
)

if TYPE_CHECKING:
    from . import ApiConfig


logger = logging.getLogger(__name__)


def get_url(config: "ApiConfig", path: str = "") -> str:
    """Resolve test/production URLs based on the api config."""
    return f"{config.url}{path}"


def _request(
    config: "ApiConfig",
    method: str,
    path: str = "",
    json: Optional[dict] = None,
) -> requests.Response:
    trace_name = f"np-atobarai.request.{path.lstrip('/')}"
    with np_atobarai_opentracing_trace(trace_name):
        response = requests.request(
            method=method,
            url=get_url(config, path),
            timeout=REQUEST_TIMEOUT,
            json=json or {},
            auth=HTTPBasicAuth(config.merchant_code, config.sp_code),
            headers={"X-NP-Terminal-Id": config.terminal_id},
        )
        # NP Atobarai returns error codes with http status code 400
        # Because we want to pass those errors to the end user,
        # we treat 400 as valid response.
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
        logger.warning("Cannot connect to NP Atobarai.", exc_info=True)
        return NPResponse({}, [NP_CONNECTION_ERROR])


def handle_unrecoverable_state(
    order: Optional[Order],
    action: str,
    transaction_id: str,
    error_codes: Iterable[str],
) -> None:
    message = f"Payment #{transaction_id} {action.capitalize()} Unrecoverable Error"
    logger.error("%s: %s", message, ", ".join(error_codes))
    if order:
        notify_dashboard(order, message)


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
    try:
        with Posuto() as pp:
            jap_ad = pp.get(ad.postal_code)
    except KeyError:
        logger.warning("Invalid japanese postal code: %s", ad.postal_code)
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


def _get_goods_name(line: PaymentLineData, config: "ApiConfig") -> str:
    if not config.sku_as_name:
        return line.product_name
    elif sku := line.product_sku:
        return sku
    return str(line.variant_id)


def _get_voucher_and_shipping_goods(
    config: "ApiConfig",
    payment_information: PaymentData,
) -> List[dict]:
    """Convert voucher and shipping amount into NP Atobarai goods lines."""
    goods_lines = []
    voucher_amount = payment_information.lines_data.voucher_amount
    if voucher_amount:
        goods_lines.append(
            {
                "goods_name": "Voucher",
                "goods_price": format_price(
                    voucher_amount, payment_information.currency
                ),
                "quantity": 1,
            }
        )
    shipping_amount = payment_information.lines_data.shipping_amount
    if shipping_amount:
        goods_lines.append(
            {
                "goods_name": "Shipping",
                "goods_price": format_price(
                    shipping_amount, payment_information.currency
                ),
                "quantity": 1,
            }
        )

    return goods_lines


def get_goods_with_refunds(
    config: "ApiConfig",
    payment: Payment,
    payment_information: PaymentData,
) -> Tuple[List[dict], Decimal]:
    """Combine PaymentLinesData and RefundData into NP Atobarai's goods list.

    Used for payment updates.
    Returns current state of order lines after refunds and total order amount.
    """
    goods_lines = []
    refund_data = payment_information.refund_data or RefundData()

    order = payment.order
    if not order:
        raise PaymentError("Cannot refund payment without order.")

    refunded_lines = create_refunded_lines(order, refund_data)

    total = Decimal("0.00")
    for line in payment_information.lines_data.lines:
        quantity = line.quantity
        refunded_quantity = refunded_lines.get(line.variant_id)
        if refunded_quantity:
            quantity -= refunded_quantity

        if quantity:
            goods_lines.append(
                {
                    "goods_name": _get_goods_name(line, config),
                    "goods_price": format_price(
                        line.amount, payment_information.currency
                    ),
                    "quantity": quantity,
                }
            )
            total += line.amount * quantity

    goods_lines.extend(_get_voucher_and_shipping_goods(config, payment_information))
    total += payment_information.lines_data.shipping_amount
    total += payment_information.lines_data.voucher_amount

    billed_amount = payment.captured_amount - payment_information.amount
    # NP requires that the sum of all goods prices is equal to billing amount
    refunded_manual_amount = billed_amount - total

    if refunded_manual_amount:
        goods_lines.append(
            {
                "goods_name": "Discount",
                "goods_price": format_price(
                    refunded_manual_amount, payment_information.currency
                ),
                "quantity": 1,
            }
        )

    return goods_lines, billed_amount


def get_goods(config: "ApiConfig", payment_information: PaymentData) -> List[dict]:
    """Convert PaymentLinesData into NP Atobarai's goods list.

    Used for initial payment registration only.
    """
    return [
        {
            "quantity": line.quantity,
            "goods_name": _get_goods_name(line, config),
            "goods_price": format_price(line.amount, payment_information.currency),
        }
        for line in payment_information.lines_data.lines
    ] + _get_voucher_and_shipping_goods(config, payment_information)


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
        return error_np_response(NO_BILLING_ADDRESS)
    if not shipping:
        return error_np_response(NO_SHIPPING_ADDRESS)

    formatted_billing = format_address(config, billing)
    formatted_shipping = format_address(config, shipping)

    if not formatted_billing:
        return error_np_response(BILLING_ADDRESS_INVALID)
    if not formatted_shipping:
        return error_np_response(SHIPPING_ADDRESS_INVALID)

    data = {
        "transactions": [
            {
                "shop_transaction_id": payment_information.payment_id,
                "shop_order_date": order_date,
                "settlement_type": NP_ATOBARAI,
                "billed_amount": billed_amount,
                "customer": {
                    "customer_name": format_name(billing),
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
    shipping_company_code: Optional[str],
    psp_reference: Optional[str],
    shipping_slip_number: Optional[str],
) -> NPResponse:
    if not shipping_company_code:
        return error_np_response(SHIPPING_COMPANY_CODE_INVALID)

    if not psp_reference:
        return error_np_response(NO_PSP_REFERENCE)

    if not shipping_slip_number:
        return error_np_response(NO_TRACKING_NUMBER)

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
