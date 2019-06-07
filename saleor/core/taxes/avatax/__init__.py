import json
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache
from requests.auth import HTTPBasicAuth

from .. import charge_taxes_on_shipping, include_taxes_in_prices

if TYPE_CHECKING:
    from ....checkout.models import Checkout
    from ....order.models import Order


common_carrier_code = "FR020100"  # FIXME
cache_key = "avatax_request_id_"  # FIXME


class TransactionType:
    INVOICE = "SalesInvoice"
    ORDER = "SalesOrder"


def get_api_url() -> str:
    """Based on settings return sanbox or production url"""
    if settings.AVATAX_USE_SANDBOX:
        return "https://sandbox-rest.avatax.com/api/v2/"
    return "https://rest.avatax.com/api/v2/"


def api_post_request(
    url: str,
    data: Dict[str, Any],
    username: str = settings.AVATAX_USERNAME_OR_ACCOUNT,
    password: str = settings.AVATAX_PASSWORD_OR_LICENSE,
) -> Dict[str, Any]:
    try:
        auth = HTTPBasicAuth(username, password)
        response = requests.post(url, auth=auth, data=json.dumps(data))  # FIXME timeout
    except requests.exceptions.RequestException:
        return {}
    return response.json()


def api_get_request(
    url,
    username=settings.AVATAX_USERNAME_OR_ACCOUNT,
    password=settings.AVATAX_PASSWORD_OR_LICENSE,
):
    return requests.get(url, auth=HTTPBasicAuth(username, password))


def validate_order(order: "Order") -> bool:
    """Validate if checkout object contains enough information to generate a request to
    avatax"""
    if not order.lines.count():
        return False
    shipping_address = order.shipping_address
    is_shipping_required = order.is_shipping_required()
    address = shipping_address or order.billing_address

    if not is_shipping_required and not address:
        return False
    if not shipping_address:
        return False
    return True


def validate_checkout(checkout: "Checkout") -> bool:
    """Validate if checkout object contains enough information to generate a request to
    avatax"""
    if not checkout.lines.count():
        return False

    shipping_address = checkout.shipping_address
    is_shipping_required = checkout.is_shipping_required
    address = shipping_address or checkout.billing_address
    if not is_shipping_required and not address:
        return False
    if not shipping_address:
        return False
    return True


def checkout_needs_new_fetch(data, checkout_token: str) -> bool:
    """We store the response from avatax for checkout object for given time. If object
    doesn't exist in cache or something has changed, then we fetch data from avatax."""
    checkout_cache_key = cache_key + checkout_token
    cached_checkout = cache.get(checkout_cache_key)

    if not cached_checkout:
        return True

    cached_request_data, cached_response = cached_checkout
    if data != cached_request_data:
        return True
    return False


def taxes_need_new_fetch(data: Dict[str, Any], taxes_token: str) -> bool:
    """We store the response from avatax. If object doesn't exist in cache or
    something has changed, then we fetch data from avatax."""
    taxes_cache_key = cache_key + taxes_token
    cached_data = cache.get(taxes_cache_key)

    if not cached_data:
        return True

    cached_request_data, _ = cached_data
    if data != cached_request_data:
        return True
    return False


def append_line_to_data(
    data: List[Dict[str, str]],
    quantity: int,
    amount: str,
    tax_code: str,
    item_code: str,
    description: str = None,
):
    data.append(
        {
            "quantity": quantity,
            "amount": str(amount),
            "taxCode": tax_code,
            "taxIncluded": include_taxes_in_prices(),
            # FIXME Should fetch taxcode from somewhere and save inside variant/product
            "itemCode": item_code,
            "description": description[:2000] if description else "",
        }
    )


def get_checkout_lines_data(
    checkout: "Checkout", discounts=None
) -> List[Dict[str, str]]:
    data = []
    lines = checkout.lines.prefetch_related(
        "variant__product__category",
        "variant__product__collections",
        "variant__product__product_type",
    )
    for line in lines:
        if not line.variant.product.charge_taxes:
            continue
        description = line.variant.product.description
        append_line_to_data(
            data=data,
            quantity=line.quantity,
            amount=str(line.get_total(discounts).amount),
            # FIXME Should fetch taxcode from somewhere and save inside variant/product
            tax_code="PC040156",
            item_code=line.variant.sku,
            description=description,
        )

    if charge_taxes_on_shipping() and checkout.shipping_method:
        append_line_to_data(
            data,
            quantity=1,
            amount=str(checkout.shipping_method.price.amount),
            tax_code=common_carrier_code,
            item_code="Shipping",
        )
    return data


def get_order_lines_data(order: "Order") -> List[Dict[str, str]]:
    data = []
    lines = order.lines.prefetch_related(
        "variant__product__category",
        "variant__product__collections",
        "variant__product__product_type",
    )
    for line in lines:
        if not line.variant.product.charge_taxes:
            continue
        append_line_to_data(
            data=data,
            quantity=line.quantity,
            amount=line.unit_price_net.amount * line.quantity,
            tax_code="PC040156",
            item_code=line.variant.sku,
            description=line.variant.product.description,
        )
    if charge_taxes_on_shipping() and order.shipping_method:
        append_line_to_data(
            data,
            quantity=1,
            amount=order.shipping_method.price.amount,
            tax_code=common_carrier_code,
            item_code="Shipping",
        )
    return data


def generate_request_data(
    transaction_type: str,
    lines: List[Dict[str, Any]],
    transaction_token: str,
    address: Dict[str, str],
    customer_code: Optional[int],
    customer_email: str,
    commit=False,
):
    data = {
        "companyCode": settings.AVATAX_COMPANY_NAME,
        "type": transaction_type,
        "lines": lines,
        "code": transaction_token,
        "date": str(date.today()),
        "customerCode": customer_code,
        # 'salespersonCode'
        # 'customerUsageType'
        # 'entityUseCode'
        # 'discount'
        # 'purchaseOrderNo'
        # 'exemptionNo'
        "addresses": {
            # FIXME we should put company address here
            "shipFrom": {  # warehouse
                "line1": "2000 Main Street",
                "city": "Irvine",
                "region": "CA",
                "country": "US",
                "postalCode": "92614",
            },
            "shipTo": {
                "line1": address.get("street_address_1"),
                "line2": address.get("street_address_2"),
                "city": address.get("city"),
                "region": address.get("country_area"),
                "country": address.get("country"),
                "postalCode": address.get("postal_code"),
            },
        },
        # parameters
        # referenceCode
        # reportingLocationCode
        # isSellerImporterOfRecord
        # businessIdentificationNo
        "commit": commit,
        # batchCode
        "currencyCode": settings.DEFAULT_CURRENCY,
        "email": customer_email,
    }
    return {"createTransactionModel": data}


def generate_request_data_from_checkout(
    checkout: "Checkout",
    transaction_token=None,
    transaction_type=TransactionType.ORDER,
    commit=False,
    discounts=None,
):

    address = checkout.shipping_address or checkout.billing_address
    lines = get_checkout_lines_data(checkout, discounts)
    data = generate_request_data(
        transaction_type=transaction_type,
        lines=lines,
        transaction_token=transaction_token or str(checkout.token),
        address=address.as_data(),
        customer_code=checkout.user.id if checkout.user else None,
        customer_email=checkout.email,
        commit=commit,
    )
    return data


def get_cached_response_or_fetch(data, token_in_cache):
    """Try to find response in cache. Return cached response if requests data are
    the same. Fetch new data in other cases"""
    data_cache_key = cache_key + token_in_cache
    if taxes_need_new_fetch(data, token_in_cache):
        transaction_url = urljoin(get_api_url(), "transactions/createoradjust")
        print("HIT TO API")
        response = api_post_request(transaction_url, data)
        if response and "error" not in response:
            cache.set(data_cache_key, (data, response), settings.AVATAX_CACHE_TIME)
    else:
        _, response = cache.get(data_cache_key)

    return response


def get_checkout_tax_data(checkout: "Checkout", discounts) -> Dict[str, Any]:
    data = generate_request_data_from_checkout(checkout, discounts=discounts)
    return get_cached_response_or_fetch(data, str(checkout.token))


def get_order_tax_data(order: "Order", commit=False) -> Dict[str, Any]:
    address = order.shipping_address or order.billing_address
    lines = get_order_lines_data(order)
    transaction = (
        TransactionType.INVOICE if not order.is_draft() else TransactionType.ORDER
    )
    data = generate_request_data(
        transaction_type=transaction,
        lines=lines,
        transaction_token=order.token,
        address=address.as_data(),
        customer_code=order.user.id if order.user else None,
        customer_email=order.user_email,
        commit=commit,
    )
    response = get_cached_response_or_fetch(data, "order_%s" % order.token)
    return response
