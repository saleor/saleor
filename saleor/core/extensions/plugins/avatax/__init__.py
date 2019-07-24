import json
import logging
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.utils.translation import pgettext_lazy
from requests.auth import HTTPBasicAuth

if TYPE_CHECKING:
    from .....checkout.models import Checkout
    from .....order.models import Order

logger = logging.getLogger(__name__)

META_FIELD = "avatax"
CACHE_TIME = 60 * 60  # 1 hour
TAX_CODES_CACHE_TIME = 60 * 60 * 24 * 7  # 7 days
CACHE_KEY = "avatax_request_id_"
TAX_CODES_CACHE_KEY = "avatax_tax_codes_cache_key"
TIMEOUT = 10  # API HTTP Requests Timeout

# Common carrier code used to identify the line as a shipping service
COMMON_CARRIER_CODE = "FR020100"

# Common discount code use to apply discount on order
COMMON_DISCOUNT_VOUCHER_CODE = "OD010000"


class TransactionType:
    INVOICE = "SalesInvoice"
    ORDER = "SalesOrder"


class CustomerErrors:
    DEFAULT_MSG = pgettext_lazy(
        "We are not able to calculate taxes for your order. Please try later"
    )
    ERRORS = ("InvalidPostalCode", "InvalidAddress", "MissingAddress")

    @classmethod
    def get_error_msg(cls, error: dict) -> str:
        error_code = error.get("code")
        if error_code in cls.ERRORS:
            return error.get("message", cls.DEFAULT_MSG)
        return cls.DEFAULT_MSG


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
        response = requests.post(url, auth=auth, data=json.dumps(data), timeout=TIMEOUT)
        logger.debug("Hit to Avatax to calculate taxes %s", url)
    except requests.exceptions.RequestException:
        logger.warning("Fetching taxes failed %s", url)
        return {}
    return response.json()


def api_get_request(
    url: str,
    username: str = settings.AVATAX_USERNAME_OR_ACCOUNT,
    password: str = settings.AVATAX_PASSWORD_OR_LICENSE,
):
    try:
        auth = HTTPBasicAuth(username, password)
        response = requests.get(url, auth=auth, timeout=TIMEOUT)
        logger.debug("[GET] Hit to %s", url)
    except requests.exceptions.RequestException:
        logger.warning("Failed to fetch data from %s", url)
        return {}
    return response.json()


def _validate_order(order: "Order") -> bool:
    """Validate if order object contains enough information to generate a request to
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
    if not order.shipping_method:
        return False
    return True


def _validate_checkout(checkout: "Checkout") -> bool:
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
    if not checkout.shipping_method:
        return False
    return True


def _retrieve_from_cache(token):
    taxes_cache_key = CACHE_KEY + token
    cached_data = cache.get(taxes_cache_key)
    return cached_data


def checkout_needs_new_fetch(data, checkout_token: str) -> bool:
    """We store the response from avatax for checkout object for given time. If object
    doesn't exist in cache or something has changed, then we fetch data from avatax."""

    cached_checkout = _retrieve_from_cache(checkout_token)

    if not cached_checkout:
        return True

    cached_request_data, cached_response = cached_checkout
    if data != cached_request_data:
        return True
    return False


def taxes_need_new_fetch(data: Dict[str, Any], taxes_token: str) -> bool:
    """We store the response from avatax. If object doesn't exist in cache or
    something has changed, then we fetch data from avatax."""
    cached_data = _retrieve_from_cache(taxes_token)

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
    tax_included: Optional[bool] = None,
):
    if tax_included is None:
        tax_included = Site.objects.get_current().settings.include_taxes_in_prices
    data.append(
        {
            "quantity": quantity,
            "amount": str(amount),
            "taxCode": tax_code,
            "taxIncluded": tax_included,
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
        description = line.variant.product.plain_text_description
        product = line.variant.product
        product_type = line.variant.product.product_type
        tax_code = retrieve_tax_code_from_meta(product)
        tax_code = tax_code or retrieve_tax_code_from_meta(product_type)
        append_line_to_data(
            data=data,
            quantity=line.quantity,
            amount=str(line.get_total(discounts).amount),
            tax_code=tax_code,
            item_code=line.variant.sku,
            description=description,
        )

    charge_taxes_on_shipping = (
        Site.objects.get_current().settings.charge_taxes_on_shipping
    )
    if charge_taxes_on_shipping and checkout.shipping_method:
        append_line_to_data(
            data,
            quantity=1,
            amount=str(checkout.shipping_method.price.amount),
            tax_code=COMMON_CARRIER_CODE,
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
        product = line.variant.product
        product_type = line.variant.product.product_type
        tax_code = retrieve_tax_code_from_meta(product)
        tax_code = tax_code or retrieve_tax_code_from_meta(product_type)
        append_line_to_data(
            data=data,
            quantity=line.quantity,
            amount=line.unit_price_net.amount * line.quantity,
            tax_code=tax_code,
            item_code=line.variant.sku,
            description=line.variant.product.plain_text_description,
        )
    if order.discount_amount and order.discount_amount.amount:
        append_line_to_data(
            data=data,
            quantity=1,
            amount=order.discount_amount.amount * -1,
            tax_code=COMMON_DISCOUNT_VOUCHER_CODE,
            item_code="Voucher",
            description=order.discount_name,
            tax_included=True,  # Voucher should be always applied as a gross amount
        )
    charge_taxes_on_shipping = (
        Site.objects.get_current().settings.charge_taxes_on_shipping
    )
    if charge_taxes_on_shipping and order.shipping_method:
        append_line_to_data(
            data,
            quantity=1,
            amount=order.shipping_method.price.amount,
            tax_code=COMMON_CARRIER_CODE,
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
    currency=settings.DEFAULT_CURRENCY,
):
    company_address = Site.objects.get_current().settings.company_address
    if company_address:
        company_address = company_address.as_data()
    else:
        logging.warning(
            "To correct calculate taxes by Avatax, company address should be provided "
            "in dashboard.settings."
        )
        company_address = {}

    data = {
        "companyCode": settings.AVATAX_COMPANY_NAME,
        "type": transaction_type,
        "lines": lines,
        "code": transaction_token,
        "date": str(date.today()),
        "customerCode": customer_code,
        "addresses": {
            "shipFrom": {
                "line1": company_address.get("street_address_1"),
                "line2": company_address.get("street_address_2"),
                "city": company_address.get("city"),
                "region": company_address.get("country_area"),
                "country": company_address.get("country"),
                "postalCode": company_address.get("postal_code"),
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
        "commit": commit,
        "currencyCode": currency,
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

    # FIXME after we introduce multicurrency this should be taken from Checkout obj
    currency = checkout.get_subtotal().currency
    data = generate_request_data(
        transaction_type=transaction_type,
        lines=lines,
        transaction_token=transaction_token or str(checkout.token),
        address=address.as_data(),
        customer_code=checkout.user.id if checkout.user else 0,
        customer_email=checkout.email,
        commit=commit,
        currency=currency,
    )
    return data


def get_cached_response_or_fetch(data, token_in_cache, force_refresh=False):
    """Try to find response in cache. Return cached response if requests data are
    the same. Fetch new data in other cases"""
    data_cache_key = CACHE_KEY + token_in_cache
    if taxes_need_new_fetch(data, token_in_cache) or force_refresh:
        transaction_url = urljoin(get_api_url(), "transactions/createoradjust")
        response = api_post_request(transaction_url, data)
        if response and "error" not in response:
            cache.set(data_cache_key, (data, response), CACHE_TIME)
        else:
            # cache failed response to limit hits to avatax.
            cache.set(data_cache_key, (data, response), 10)
    else:
        _, response = cache.get(data_cache_key)

    return response


def get_checkout_tax_data(checkout: "Checkout", discounts) -> Dict[str, Any]:
    data = generate_request_data_from_checkout(checkout, discounts=discounts)
    return get_cached_response_or_fetch(data, str(checkout.token))


def get_order_tax_data(
    order: "Order", commit=False, force_refresh=False
) -> Dict[str, Any]:
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
        currency=order.total.currency,
    )
    response = get_cached_response_or_fetch(
        data, "order_%s" % order.token, force_refresh
    )
    return response


def generate_tax_codes_dict(
    response: Dict[str, Union[str, int, bool]]
) -> Dict[str, str]:
    tax_codes = {}
    for line in response.get("value", []):
        if line.get("isActive"):
            tax_codes[line.get("taxCode")] = line.get("description")
    return tax_codes


def get_cached_tax_codes_or_fetch(cache_time: int = TAX_CODES_CACHE_TIME):
    """Try to get cached tax codes. If cache is empty fetch the newest taxcodes from
    avatax"""
    tax_codes = cache.get(TAX_CODES_CACHE_KEY, {})
    if not tax_codes:
        tax_codes_url = urljoin(get_api_url(), "definitions/taxcodes")
        response = api_get_request(tax_codes_url)
        if response and "error" not in response:
            tax_codes = generate_tax_codes_dict(response)
            cache.set(TAX_CODES_CACHE_KEY, tax_codes, cache_time)
    return tax_codes


def retrieve_tax_code_from_meta(obj: Union["Product", "ProductVariant"]):
    tax = obj.meta.get("taxes", {}).get(META_FIELD, {})
    # O9999999 - "Temporary Unmapped Other SKU - taxable default"
    return tax.get("code", "O9999999")
