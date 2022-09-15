import json
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union, cast
from urllib.parse import urljoin

import opentracing
import opentracing.tags
import requests
from django.contrib.sites.models import Site
from django.core.cache import cache
from requests.auth import HTTPBasicAuth

from ...account.models import Address
from ...checkout import base_calculations
from ...checkout.utils import is_shipping_required
from ...core.taxes import TaxError
from ...discount import OrderDiscountType, VoucherType
from ...order import base_calculations as base_order_calculations
from ...order.utils import (
    get_total_order_discount_excluding_shipping,
    get_voucher_discount_assigned_to_order,
)
from ...shipping.models import ShippingMethod, ShippingMethodChannelListing
from ...warehouse.models import Warehouse

if TYPE_CHECKING:
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...order.models import Order
    from ...product.models import Product, ProductType, ProductVariant

logger = logging.getLogger(__name__)

META_CODE_KEY = "avatax.code"
META_DESCRIPTION_KEY = "avatax.description"
CACHE_TIME = 60 * 60  # 1 hour
TAX_CODES_CACHE_TIME = 60 * 60 * 24 * 7  # 7 days
CACHE_KEY = "avatax_request_id_"
TAX_CODES_CACHE_KEY = "avatax_tax_codes_cache_key"
TIMEOUT = 10  # API HTTP Requests Timeout

# Common discount code use to apply discount on order
COMMON_DISCOUNT_VOUCHER_CODE = "OD010000"

# Temporary Unmapped Other SKU - taxable default
DEFAULT_TAX_CODE = "O9999999"
DEFAULT_TAX_DESCRIPTION = "Unmapped Other SKU - taxable default"


@dataclass
class AvataxConfiguration:
    username_or_account: str
    password_or_license: str
    from_street_address: str
    from_city: str
    from_country: str
    from_postal_code: str
    from_country_area: str = ""
    use_sandbox: bool = True
    company_name: str = "DEFAULT"
    autocommit: bool = False
    shipping_tax_code: str = ""
    override_global_tax: bool = False
    include_taxes_in_prices: bool = True

    @property
    def tax_included(self) -> bool:
        return (
            self.include_taxes_in_prices
            if self.override_global_tax
            else Site.objects.get_current().settings.include_taxes_in_prices
        )


class TransactionType:
    INVOICE = "SalesInvoice"
    ORDER = "SalesOrder"


class CustomerErrors:
    DEFAULT_MSG = "We are not able to calculate taxes for your order. Please try later"
    ERRORS = ("InvalidPostalCode", "InvalidAddress", "MissingAddress")

    @classmethod
    def get_error_msg(cls, error: dict) -> str:
        error_code = error.get("code")
        if error_code in cls.ERRORS:
            return error.get("message", cls.DEFAULT_MSG)
        return cls.DEFAULT_MSG


def get_api_url(use_sandbox=True) -> str:
    """Based on settings return sanbox or production url."""
    if use_sandbox:
        return "https://sandbox-rest.avatax.com/api/v2/"
    return "https://rest.avatax.com/api/v2/"


def api_post_request(
    url: str, data: Dict[str, Any], config: AvataxConfiguration
) -> Dict[str, Any]:
    response = None
    try:
        auth = HTTPBasicAuth(config.username_or_account, config.password_or_license)
        response = requests.post(url, auth=auth, data=json.dumps(data), timeout=TIMEOUT)
        logger.debug("Hit to Avatax to calculate taxes %s", url)
        json_response = response.json()
        if "error" in response:  # type: ignore
            logger.exception("Avatax response contains errors %s", json_response)
            return json_response
    except requests.exceptions.RequestException:
        logger.exception("Fetching taxes failed %s", url)
        return {}
    except json.JSONDecodeError:
        content = response.content if response else "Unable to find the response"
        logger.exception(
            "Unable to decode the response from Avatax. Response: %s", content
        )
        return {}
    return json_response  # type: ignore


def api_get_request(
    url: str,
    username_or_account: str,
    password_or_license: str,
):
    response = None
    try:
        auth = HTTPBasicAuth(username_or_account, password_or_license)
        response = requests.get(url, auth=auth, timeout=TIMEOUT)
        json_response = response.json()
        logger.debug("[GET] Hit to %s", url)
        if "error" in json_response:  # type: ignore
            logger.error("Avatax response contains errors %s", json_response)
        return json_response
    except requests.exceptions.RequestException:
        logger.exception("Failed to fetch data from %s", url)
        return {}
    except json.JSONDecodeError:
        content = response.content if response else "Unable to find the response"
        logger.exception(
            "Unable to decode the response from Avatax. Response: %s", content
        )
        return {}


def _validate_adddress_details(
    shipping_address, is_shipping_required, address, delivery_method
):
    if not is_shipping_required and address:
        return True
    if not shipping_address:
        return False
    if not delivery_method:
        return False
    return True


def _validate_order(order: "Order") -> bool:
    """Validate the order object if it is ready to generate a request to avatax."""
    if not order.lines.exists():
        return False
    shipping_required = order.is_shipping_required()
    if order.collection_point_id:
        collection_point = order.collection_point
        delivery_method: Union[None, ShippingMethod, Warehouse] = collection_point
        shipping_address = collection_point.address  # type: ignore
        address = shipping_address
    else:
        delivery_method = order.shipping_method
        shipping_address = order.shipping_address
        address = shipping_address or order.billing_address
    valid_address_details = _validate_adddress_details(
        shipping_address, shipping_required, address, delivery_method
    )
    if not valid_address_details:
        return False
    if shipping_required and isinstance(delivery_method, ShippingMethod):
        channel_listing = delivery_method.channel_listings.filter(  # type: ignore
            channel_id=order.channel_id
        ).first()
        if not channel_listing:
            return False
    return True


def _validate_checkout(
    checkout_info: "CheckoutInfo", lines: Iterable["CheckoutLineInfo"]
) -> bool:
    """Validate the checkout object if it is ready to generate a request to avatax."""
    if not lines:
        return False

    shipping_required = is_shipping_required(lines)
    shipping_address = checkout_info.delivery_method_info.shipping_address
    address = shipping_address or checkout_info.billing_address
    return _validate_adddress_details(
        shipping_address,
        shipping_required,
        address,
        checkout_info.delivery_method_info.delivery_method,
    )


def taxes_need_new_fetch(data: Dict[str, Any], cached_data) -> bool:
    """Check if Avatax's taxes data need to be refetched.

    The response from Avatax is stored in a cache. If an object doesn't exist in cache
    or something has changed, taxes need to be refetched.
    """
    if not cached_data:
        return True

    cached_request_data, _ = cached_data
    if data != cached_request_data:
        return True
    return False


def append_line_to_data(
    data: List[Dict[str, Union[Any]]],
    quantity: int,
    amount: Decimal,
    tax_code: str,
    item_code: str,
    tax_included: bool,
    name: str = None,
    discounted: Optional[bool] = False,
    tax_override_data: Optional[dict] = None,
    ref1: Optional[str] = None,
    ref2: Optional[str] = None,
):
    line_data = {
        "quantity": quantity,
        "amount": str(amount),
        "taxCode": tax_code,
        "taxIncluded": tax_included,
        "itemCode": item_code,
        "discounted": discounted,
        "description": name,
    }

    if tax_override_data:
        line_data["taxOverride"] = tax_override_data
    if ref1:
        line_data["ref1"] = ref1
    if ref2:
        line_data["ref2"] = ref2
    data.append(line_data)


def append_shipping_to_data(
    data: List[Dict],
    shipping_price_amount: Optional[Decimal],
    shipping_tax_code: str,
    tax_included: bool,
    discounted: Optional[bool] = False,
):
    charge_taxes_on_shipping = (
        Site.objects.get_current().settings.charge_taxes_on_shipping
    )
    if charge_taxes_on_shipping and shipping_price_amount is not None:
        append_line_to_data(
            data,
            quantity=1,
            amount=shipping_price_amount,
            tax_code=shipping_tax_code,
            item_code="Shipping",
            tax_included=tax_included,
            discounted=discounted,
        )


def get_checkout_lines_data(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    config: AvataxConfiguration,
    tax_included: bool,
    discounts=None,
) -> List[Dict[str, Union[str, int, bool, None]]]:
    data: List[Dict[str, Union[str, int, bool, None]]] = []
    channel = checkout_info.channel
    voucher = checkout_info.voucher
    is_entire_order_discount = (
        voucher.type == VoucherType.ENTIRE_ORDER
        if voucher and not voucher.apply_once_per_order
        else False
    )
    for line_info in lines_info:
        tax_override_data = {}
        if not line_info.product.charge_taxes:
            if not is_entire_order_discount:
                continue
            # if there is a voucher for the entire order we need to attach this line
            # with 0 tax to propagate discount through all lines
            tax_override_data = {
                "type": "taxAmount",
                "taxAmount": 0,
                "reason": "Charge taxes for this product are turned off.",
            }

        product = line_info.product
        name = product.name
        product_type = line_info.product_type
        item_code = line_info.variant.sku or line_info.variant.get_global_id()
        tax_code = retrieve_tax_code_from_meta(product, default=None)
        tax_code = tax_code or retrieve_tax_code_from_meta(product_type)
        checkout_line_total = base_calculations.calculate_base_line_total_price(
            line_info,
            channel,
            discounts,
        )

        # This is a workaround for Avatax and sending a lines with amount 0. Like
        # order lines which are fully discounted for some reason. If we use a
        # standard tax_code, Avatax will raise an exception: "When shipping
        # cross-border into CIF countries, Tax Included is not supported with mixed
        # positive and negative line amounts."
        # This is also a workaround for Avatax when the tax_override_data is used.
        # Otherwise Avatax will raise an exception: "TaxIncluded is not supported in
        # combination with caps, thresholds, or base rules."
        tax_code = (
            tax_code
            if checkout_line_total.amount and not tax_override_data
            else DEFAULT_TAX_CODE
        )
        append_line_to_data_kwargs = {
            "data": data,
            "quantity": line_info.line.quantity,
            "tax_code": tax_code,
            "item_code": item_code,
            "name": name,
            "tax_included": tax_included,
            "discounted": is_entire_order_discount,
            "tax_override_data": tax_override_data,
        }

        append_line_to_data(
            **append_line_to_data_kwargs,
            amount=checkout_line_total.amount,
            ref1=line_info.variant.sku,
        )

    delivery_method = checkout_info.delivery_method_info.delivery_method
    if delivery_method:
        price = getattr(delivery_method, "price", None)
        is_shipping_discount = (
            voucher.type == VoucherType.SHIPPING if voucher else False
        )
        append_shipping_to_data(
            data,
            price.amount if price else None,
            config.shipping_tax_code,
            tax_included,
            is_shipping_discount,
        )

    return data


def get_order_lines_data(
    order: "Order", config: AvataxConfiguration, tax_included: bool, discounted: bool
) -> List[Dict[str, Union[str, int, bool, None]]]:
    data: List[Dict[str, Union[str, int, bool, None]]] = []
    lines = order.lines.prefetch_related(
        "variant__product__category",
        "variant__product__collections",
        "variant__product__product_type",
    ).filter(variant__product__charge_taxes=True)
    for line in lines:
        if not line.variant:
            continue
        product = line.variant.product
        product_type = line.variant.product.product_type
        tax_code = retrieve_tax_code_from_meta(product, default=None)
        tax_code = tax_code or retrieve_tax_code_from_meta(product_type)
        prices_data = base_order_calculations.base_order_line_total(line)

        if tax_included:
            undiscounted_amount = prices_data.undiscounted_price.gross.amount
            price_with_discounts_amount = prices_data.price_with_discounts.gross.amount
        else:
            undiscounted_amount = prices_data.undiscounted_price.net.amount
            price_with_discounts_amount = prices_data.price_with_discounts.net.amount

        append_line_to_data_kwargs = {
            "data": data,
            "quantity": line.quantity,
            # This is a workaround for Avatax and sending a lines with amount 0. Like
            # order lines which are fully discounted for some reason. If we use a
            # standard tax_code, Avatax will raise an exception: "When shipping
            # cross-border into CIF countries, Tax Included is not supported with mixed
            # positive and negative line amounts."
            "tax_code": tax_code if undiscounted_amount else DEFAULT_TAX_CODE,
            "item_code": line.variant.sku or line.variant.get_global_id(),
            "name": line.variant.product.name,
            "tax_included": tax_included,
            "discounted": discounted,
        }
        append_line_to_data(
            **append_line_to_data_kwargs,
            amount=price_with_discounts_amount,
        )

    shipping_method_channel_listing = ShippingMethodChannelListing.objects.filter(
        shipping_method=order.shipping_method_id, channel=order.channel_id
    ).first()
    if shipping_method_channel_listing:
        shipping_discount_amount = Decimal("0")
        if (
            order.voucher_id
            and order.voucher.type == VoucherType.SHIPPING  # type: ignore
        ):
            shipping_discount = get_voucher_discount_assigned_to_order(order)
            if shipping_discount:
                shipping_discount_amount = shipping_discount.amount_value
        shipping_price = max(
            shipping_method_channel_listing.price.amount - shipping_discount_amount,
            Decimal("0"),
        )
        shipping_discounted = order.discounts.filter(
            type=OrderDiscountType.MANUAL
        ).exists()
        append_shipping_to_data(
            data,
            shipping_price if shipping_price else None,
            config.shipping_tax_code,
            tax_included,
            shipping_discounted,
        )
    return data


def _is_single_location(ship_from, ship_to):
    for key, value in ship_from.items():
        if key not in ship_to:
            return False
        if not value and not ship_to[key]:
            continue
        if value is None or ship_to[key] is None:
            return False

        if value.lower() == ship_to[key].lower():
            continue
        return False
    return True


def generate_request_data(
    transaction_type: str,
    lines: List[Dict[str, Any]],
    transaction_token: str,
    address: Dict[str, str],
    customer_email: str,
    config: AvataxConfiguration,
    currency: str,
    discount: Optional[Decimal] = None,
):
    ship_from = {
        "line1": config.from_street_address,
        "line2": "",
        "city": config.from_city,
        "region": config.from_country_area,
        "country": config.from_country,
        "postalCode": config.from_postal_code,
    }
    ship_to = {
        "line1": address.get("street_address_1"),
        "line2": address.get("street_address_2"),
        "city": address.get("city"),
        "region": address.get("country_area"),
        "country": address.get("country"),
        "postalCode": address.get("postal_code"),
    }
    if _is_single_location(ship_from, ship_to):
        addresses: Dict[str, Dict] = {"singleLocation": ship_to}
    else:
        addresses = {"shipFrom": ship_from, "shipTo": ship_to}
    data = {
        "companyCode": config.company_name,
        "type": transaction_type,
        "lines": lines,
        "code": transaction_token,
        "date": str(date.today()),
        # https://developer.avalara.com/avatax/dev-guide/transactions/simple-transaction/
        "customerCode": 0,
        # https://developer.avalara.com/avatax/dev-guide/discounts-and-overrides/discounts/
        "discount": str(discount) if discount else None,
        "addresses": addresses,
        "commit": config.autocommit,
        "currencyCode": currency,
        "email": customer_email,
    }
    return {"createTransactionModel": data}


def generate_request_data_from_checkout(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    config: AvataxConfiguration,
    tax_included: bool,
    transaction_token=None,
    transaction_type=TransactionType.ORDER,
    discounts=None,
):
    shipping_address = checkout_info.delivery_method_info.shipping_address
    address = shipping_address or checkout_info.billing_address
    lines = get_checkout_lines_data(
        checkout_info, lines_info, config, tax_included, discounts
    )
    if not lines:
        return {}
    voucher = checkout_info.voucher
    # for apply_once_per_order vouchers the discount is already applied on lines
    discount_amount = (
        checkout_info.checkout.discount.amount
        if voucher
        and voucher.type != VoucherType.SPECIFIC_PRODUCT
        and not voucher.apply_once_per_order
        else 0
    )

    currency = checkout_info.checkout.currency
    customer_email = cast(str, checkout_info.get_customer_email())
    data = generate_request_data(
        transaction_type=transaction_type,
        lines=lines,
        transaction_token=transaction_token or str(checkout_info.checkout.token),
        address=address.as_data() if address else {},
        customer_email=customer_email,
        discount=discount_amount,
        config=config,
        currency=currency,
    )
    return data


def _fetch_new_taxes_data(
    data: Dict[str, Dict], data_cache_key: str, config: AvataxConfiguration
):
    transaction_url = urljoin(
        get_api_url(config.use_sandbox), "transactions/createoradjust"
    )
    with opentracing.global_tracer().start_active_span(
        "avatax.transactions.crateoradjust"
    ) as scope:
        span = scope.span
        span.set_tag(opentracing.tags.COMPONENT, "tax")
        span.set_tag("service.name", "avatax")
        response = api_post_request(transaction_url, data, config)
    if response and "error" not in response:
        cache.set(data_cache_key, (data, response), CACHE_TIME)
    else:
        # cache failed response to limit hits to avatax.
        cache.set(data_cache_key, (data, response), 10)
    return response


def get_cached_response_or_fetch(
    data: Dict[str, Dict],
    token_in_cache: str,
    config: AvataxConfiguration,
    force_refresh: bool = False,
):
    """Try to find response in cache.

    Return cached response if requests data are the same. Fetch new data in other cases.
    """
    # if the data is empty it means there is nothing to send to avalara
    if not data:
        return None
    data_cache_key = CACHE_KEY + token_in_cache
    cached_data = cache.get(data_cache_key)
    if taxes_need_new_fetch(data, cached_data) or force_refresh:
        response = _fetch_new_taxes_data(data, data_cache_key, config)
    else:
        _, response = cached_data
    return response


def get_checkout_tax_data(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    tax_included: bool,
    discounts,
    config: AvataxConfiguration,
) -> Dict[str, Any]:
    data = generate_request_data_from_checkout(
        checkout_info, lines_info, config, tax_included, discounts=discounts
    )
    return get_cached_response_or_fetch(data, str(checkout_info.checkout.token), config)


def get_order_request_data(
    order: "Order", config: AvataxConfiguration, tax_included: bool
):
    if order.collection_point_id:
        address: Address = order.collection_point.address  # type: ignore
    else:
        address = order.shipping_address or order.billing_address  # type: ignore

    transaction = (
        TransactionType.INVOICE
        if not (order.is_draft() or order.is_unconfirmed())
        else TransactionType.ORDER
    )
    discount_amount = get_total_order_discount_excluding_shipping(order).amount
    discounted_lines = discount_amount != Decimal("0")
    lines = get_order_lines_data(
        order, config, tax_included, discounted=discounted_lines
    )
    # if there is no lines to sent we do not want to send the request to avalara
    if not lines:
        return {}
    data = generate_request_data(
        transaction_type=transaction,
        lines=lines,
        transaction_token=str(order.id),
        address=address.as_data() if address else {},
        customer_email=order.user_email,
        config=config,
        currency=order.currency,
        discount=discount_amount,
    )
    return data


def get_order_tax_data(
    order: "Order", config: AvataxConfiguration, tax_included: bool, force_refresh=False
) -> Dict[str, Any]:
    data = get_order_request_data(order, config, tax_included)
    response = get_cached_response_or_fetch(
        data, "order_%s" % order.id, config, force_refresh
    )
    if response and "error" in response:
        raise TaxError(response.get("error"))
    return response


def generate_tax_codes_dict(response: Dict[str, Any]) -> Dict[str, str]:
    tax_codes = {}
    for line in response.get("value", []):
        if line.get("isActive"):
            tax_codes[line.get("taxCode")] = line.get("description")
    return tax_codes


def get_cached_tax_codes_or_fetch(
    config: AvataxConfiguration, cache_time: int = TAX_CODES_CACHE_TIME
):
    """Try to get cached tax codes.

    If the cache is empty, fetch the newest taxcodes from avatax.
    """
    tax_codes = cache.get(TAX_CODES_CACHE_KEY, {})
    if not tax_codes:
        tax_codes_url = urljoin(get_api_url(config.use_sandbox), "definitions/taxcodes")
        with opentracing.global_tracer().start_active_span(
            "avatax.definitions.taxcodes"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "tax")
            span.set_tag("service.name", "avatax")
            response = api_get_request(
                tax_codes_url, config.username_or_account, config.password_or_license
            )
        if response and "error" not in response:
            tax_codes = generate_tax_codes_dict(response)
            cache.set(TAX_CODES_CACHE_KEY, tax_codes, cache_time)
    return tax_codes


def retrieve_tax_code_from_meta(
    obj: Union["Product", "ProductVariant", "ProductType"],
    default: Optional[str] = DEFAULT_TAX_CODE,
):
    tax_code = obj.get_value_from_metadata(META_CODE_KEY, default)
    return tax_code
