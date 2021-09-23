from typing import Optional

import requests
from django.utils import timezone
from requests.auth import HTTPBasicAuth

from saleor.checkout.calculations import checkout_line_total
from saleor.checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from saleor.checkout.models import Checkout
from saleor.discount.utils import fetch_active_discounts
from saleor.payment import PaymentError
from saleor.payment.gateways.np_atobarai.api_types import ApiConfig, PaymentResult
from saleor.payment.gateways.np_atobarai.const import NP_ATOBARAI
from saleor.payment.interface import AddressData, PaymentData
from saleor.payment.utils import price_to_minor_unit
from saleor.plugins.manager import get_plugins_manager

REQUEST_TIMEOUT = 15


def get_url(config: ApiConfig, path="") -> str:
    """Resolve test/production URLs based on the api config."""
    if config.test_mode:
        return f"https://ctcp.np-payment-gateway.com/v1{path}"
    return f"https://cp.np-payment-gateway.com/v1{path}"


def _request(
    config: ApiConfig, method: str, path="", json: Optional[dict] = None
) -> requests.Response:
    if json is None:
        json = {}
    return requests.request(
        method=method,
        url=get_url(config, path),
        timeout=REQUEST_TIMEOUT,
        json=json,
        auth=HTTPBasicAuth(config.merchant_code, config.sp_code),
        headers={"X-NP-Terminal-Id": config.terminal_id},
    )


def health_check(config: ApiConfig) -> bool:
    response = _request(config, "post", "/authorizations/find")
    return response.status_code not in [401, 403]


def _format_name(ad: AddressData):
    """Follow the japanese name guidelines."""
    return f"{ad.first_name} {ad.last_name}".lstrip().rstrip()


def _format_address(ad: AddressData):
    """Follow the japanese address guidelines."""
    return (
        f"{ad.country} {ad.country_area} {ad.city} {ad.city_area} "
        f"{ad.street_address_1} {ad.street_address_2}"
    )


def _get_items(payment_information: "PaymentData"):
    checkout = Checkout.objects.filter(
        payments__id=payment_information.payment_id
    ).first()

    if not checkout:
        raise PaymentError("Unable to calculate products for NP.")

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    discounts = fetch_active_discounts()
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    currency = payment_information.currency

    line_items = []
    for line_info in lines:
        total = checkout_line_total(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            checkout_line_info=line_info,
            discounts=discounts,
        )
        address = checkout_info.shipping_address or checkout_info.billing_address
        unit_price = manager.calculate_checkout_line_unit_price(
            total,
            line_info.line.quantity,
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        )
        unit_gross = unit_price.gross.amount

        line_data = {
            "quantity": line_info.line.quantity,
            "goods_name": f"{line_info.variant.product.name}, {line_info.variant.name}",
            "goods_price": price_to_minor_unit(unit_gross, currency),
        }
        line_items.append(line_data)

    return line_items


def register_transaction(
    config: ApiConfig, payment_information: "PaymentData"
) -> PaymentResult:
    order_date = timezone.now().strftime("%Y-%m-%d")
    assert payment_information.billing
    assert payment_information.shipping
    data = {
        "transactions": [
            {
                "shop_transaction_id": payment_information.token,
                "shop_order_date": order_date,
                "settlement_type": NP_ATOBARAI,
                "billed_amount": payment_information.amount,
                "customer": {
                    "customer_name": payment_information.billing.first_name,
                    "company_name": payment_information.billing.company_name,
                    "zip_code": payment_information.billing.postal_code,
                    "address": _format_address(payment_information.billing),
                    "tel": payment_information.billing.phone,
                    "email": payment_information.customer_email,
                },
                "dest_customer": {
                    "customer_name": _format_name(payment_information.shipping),
                    "company_name": payment_information.shipping.company_name,
                    "zip_code": payment_information.shipping.postal_code,
                    "address": _format_address(payment_information.shipping),
                    "tel": payment_information.shipping.phone,
                    "email": payment_information.customer_email,
                },
                "goods": _get_items(payment_information),
            },
        ]
    }

    response_data = _request(config, "post", "/transactions", json=data).json()
    return PaymentResult(
        status=response_data["authori_result"],
        psp_reference=response_data["np_transaction_id"],
    )
