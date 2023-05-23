import dataclasses
import json
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin

import opentracing
import opentracing.tags
import requests
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from requests.auth import HTTPBasicAuth

from ...checkout import base_calculations
from ...checkout.models import Checkout
from ...core.taxes import TaxError
from ...order.utils import get_total_order_discount
from ...plugins.avatax import CACHE_KEY, CACHE_TIME, taxes_need_new_fetch

if TYPE_CHECKING:
    from ...account.models import Address
    from ...channel.models import Channel
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...order.models import Order
    from ...product.models import (
        ProductType,
        ProductVariant,
        ProductVariantChannelListing,
    )

logger = logging.getLogger(__name__)


# Must be DIRECT for direct to consumer e-commerece
TRANSACTION_TYPE = "DIRECT"
SHIPPING_UNIT_OF_MEASURE = "EA"

# The identifiers for tax types that we would need to group
# for the tax breakdown
SALES_TAX = "S"
USE_TAX = "U"


@dataclass
class AvataxConfiguration:
    username_or_account: str
    password_or_license: str
    use_sandbox: bool = True
    company_name: str = "DEFAULT"
    autocommit: bool = False
    shipping_product_code: str = "TAXFREIGHT"


@dataclass
class TransactionLine:
    InvoiceLine: Optional[int]
    ProductCode: str
    UnitPrice: Optional[Decimal]
    UnitOfMeasure: Optional[str]
    BilledUnits: Optional[Decimal]
    LineAmount: Optional[Decimal]
    AlternateUnitPrice: Optional[Decimal]
    TaxIncluded: bool
    UnitQuantity: Optional[int]
    UnitQuantityUnitOfMeasure: Optional[str]
    DestinationCountryCode: str
    """ISO 3166-1 alpha-3 code"""
    DestinationJurisdiction: str
    DestinationAddress1: Optional[str]
    DestinationAddress2: Optional[str]
    DestinationCounty: Optional[str]
    DestinationCity: str
    DestinationPostalCode: str
    SaleCountryCode: str
    SaleAddress1: Optional[str]
    SaleAddress2: Optional[str]
    SaleJurisdiction: str
    SaleCounty: Optional[str]
    SaleCity: str
    SalePostalCode: str
    Discounted: Optional[bool] = False

    OriginCountryCode: Optional[str] = None
    OriginJurisdiction: Optional[str] = None
    OriginCounty: Optional[str] = None
    OriginCity: Optional[str] = None
    OriginPostalCode: Optional[str] = None
    OriginAddress1: Optional[str] = None
    OriginAddress2: Optional[str] = None

    UserData: Optional[str] = None
    CustomString1: Optional[str] = None
    CustomString2: Optional[str] = None
    CustomString3: Optional[str] = None
    CustomNumeric1: Optional[Decimal] = None
    CustomNumeric2: Optional[Decimal] = None
    CustomNumeric3: Optional[Decimal] = None


@dataclass
class TransactionCreateRequestData:
    EffectiveDate: str
    InvoiceDate: str
    TitleTransferCode: str
    TransactionType: str
    TransactionLines: List[TransactionLine]
    InvoiceNumber: Optional[str] = None
    Discount: Optional[Decimal] = Decimal("0.00")
    UserTranId: Optional[str] = None


def get_metadata_key(key_name: str):
    """Namespace metadata key names: PLUGIN_ID:Key."""
    return "mirumee.taxes.avalara_excise:" + key_name


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


def get_api_url(use_sandbox=True) -> str:
    """Based on settings return sanbox or production url."""
    if use_sandbox:
        return "https://excisesbx.avalara.com/api/v1/"
    return "https://excise.avalara.com/api/v1/"


def api_post_request(
    url: str, data: Optional[Dict[str, Any]], config: AvataxConfiguration
) -> Dict[str, Any]:
    response = None
    try:
        auth = HTTPBasicAuth(config.username_or_account, config.password_or_license)
        headers = {
            "x-company-id": config.company_name,
            "Content-Type": "application/json",
        }
        formatted_data = json.dumps(data, cls=EnhancedJSONEncoder)
        response = requests.post(
            url,
            headers=headers,
            auth=auth,
            data=formatted_data,
            timeout=30,
            allow_redirects=False,
        )
        logger.debug("Hit to Avatax Excise API with URL: %s", url)
        if response.status_code == 401:
            logger.exception("Avatax Excise Authentication Error - Invalid Credentials")
            return {}
        json_response = response.json()
        if json_response.get("Status") == "Errors found":
            logger.exception("Avatax Excise response contains errors %s", json_response)
            return json_response

    except requests.exceptions.RequestException:
        logger.exception("Excise API request failed for URL: %s", url)
        return {}
    except json.JSONDecodeError:
        content = "Unable to find the response"
        if response:
            content = response.content  # type: ignore
        logger.exception(
            "Unable to decode the response from Avatax Excise. " "Response: %s",
            content,
        )
        return {}
    return json_response  # type: ignore


def append_line_to_data(
    data: List[TransactionLine],
    line_id: int,
    quantity: int,
    amount: Decimal,
    tax_included: bool,
    variant: "ProductVariant",
    shipping_address: "Address",
    variant_channel_listing: "ProductVariantChannelListing",
    channel: "Channel",
    discounted: bool = False,
    product_type: Optional["ProductType"] = None,
):
    """Append Checkout or Order line data."""

    stock = variant.stocks.for_channel_and_country(  # type: ignore
        channel.slug, shipping_address.country
    ).first()
    warehouse_address = stock.warehouse.address if stock else None

    # ensure that if the product_type is provided, we use that
    # otherwise fallback to getting it from varint instance
    product_type = product_type or variant.product.product_type

    unit_quantity = variant.get_value_from_private_metadata(
        get_metadata_key("UnitQuantity")
    )
    unit_of_measure = product_type.get_value_from_private_metadata(
        get_metadata_key("UnitOfMeasure")
    )
    unit_quantity_of_measure = product_type.get_value_from_private_metadata(
        get_metadata_key("UnitQuantityUnitOfMeasure")
    )

    origin_country_code = None
    origin_jurisdiction = None
    origin_address1 = None
    origin_address2 = None
    origin_city = None
    origin_county = None
    origin_postal_code = None

    if warehouse_address:
        origin_country_code = warehouse_address.country.alpha3
        origin_jurisdiction = warehouse_address.country_area
        origin_address1 = warehouse_address.street_address_1
        origin_address2 = warehouse_address.street_address_2
        origin_city = warehouse_address.city
        origin_county = warehouse_address.city_area
        origin_postal_code = warehouse_address.postal_code

    transaction_line = TransactionLine(
        InvoiceLine=line_id,
        ProductCode=variant.sku or variant.get_global_id(),
        UnitPrice=amount,
        UnitOfMeasure=unit_of_measure,
        BilledUnits=Decimal(quantity),
        LineAmount=amount,
        AlternateUnitPrice=variant_channel_listing.cost_price_amount,
        TaxIncluded=tax_included,
        UnitQuantity=unit_quantity,
        UnitQuantityUnitOfMeasure=unit_quantity_of_measure,
        DestinationCountryCode=shipping_address.country.alpha3,
        DestinationJurisdiction=shipping_address.country_area,
        DestinationAddress1=shipping_address.street_address_1,
        DestinationAddress2=shipping_address.street_address_2,
        DestinationCity=shipping_address.city,
        DestinationCounty=shipping_address.city_area,
        DestinationPostalCode=shipping_address.postal_code,
        SaleCountryCode=shipping_address.country.alpha3,
        SaleJurisdiction=shipping_address.country_area,
        SaleAddress1=shipping_address.street_address_1,
        SaleAddress2=shipping_address.street_address_2,
        SaleCity=shipping_address.city,
        SaleCounty=shipping_address.city_area,
        SalePostalCode=shipping_address.postal_code,
        OriginCountryCode=origin_country_code,
        OriginJurisdiction=origin_jurisdiction,
        OriginAddress1=origin_address1,
        OriginAddress2=origin_address2,
        OriginCity=origin_city,
        OriginCounty=origin_county,
        OriginPostalCode=origin_postal_code,
        UserData=variant.sku,
        Discounted=discounted,
        CustomString1=variant.get_value_from_private_metadata(
            get_metadata_key("CustomString1")
        ),
        CustomString2=variant.get_value_from_private_metadata(
            get_metadata_key("CustomString2")
        ),
        CustomString3=variant.get_value_from_private_metadata(
            get_metadata_key("CustomString3")
        ),
        CustomNumeric1=variant.get_value_from_private_metadata(
            get_metadata_key("CustomNumeric1")
        ),
        CustomNumeric2=variant.get_value_from_private_metadata(
            get_metadata_key("CustomNumeric2")
        ),
        CustomNumeric3=variant.get_value_from_private_metadata(
            get_metadata_key("CustomNumeric3")
        ),
    )

    data.append(transaction_line)


def append_shipping_to_data(
    data: List[TransactionLine],
    shipping_product_code: str,
    shipping_address: "Address",
    shipping_price_amount: Optional[Decimal],
):
    charge_taxes_on_shipping = (
        Site.objects.get_current().settings.charge_taxes_on_shipping
    )
    if charge_taxes_on_shipping and shipping_price_amount:
        data.append(
            TransactionLine(
                InvoiceLine=None,
                ProductCode=shipping_product_code,
                UnitPrice=None,
                UnitOfMeasure=SHIPPING_UNIT_OF_MEASURE,
                BilledUnits=None,
                LineAmount=shipping_price_amount,
                AlternateUnitPrice=None,
                TaxIncluded=False,
                UnitQuantity=None,
                UnitQuantityUnitOfMeasure=None,
                DestinationCountryCode=shipping_address.country.alpha3,
                DestinationJurisdiction=shipping_address.country_area,
                DestinationAddress1=shipping_address.street_address_1,
                DestinationAddress2=shipping_address.street_address_2,
                DestinationCity=shipping_address.city,
                DestinationCounty=shipping_address.city_area,
                DestinationPostalCode=shipping_address.postal_code,
                SaleCountryCode=shipping_address.country.alpha3,
                SaleJurisdiction=shipping_address.country_area,
                SaleAddress1=shipping_address.street_address_1,
                SaleAddress2=shipping_address.street_address_2,
                SaleCity=shipping_address.city,
                SaleCounty=shipping_address.city_area,
                SalePostalCode=shipping_address.postal_code,
                UserData="Shipping",
            )
        )


def generate_request_data(
    transaction_type: str,
    lines: List[TransactionLine],
    invoice_number: Optional[str],
    user_tran_id: Optional[str] = None,
    discount: Optional[Decimal] = Decimal("0.00"),
):

    today_date = str(timezone.now().date())
    data = TransactionCreateRequestData(
        EffectiveDate=today_date,
        InvoiceDate=today_date,
        InvoiceNumber=invoice_number,
        TitleTransferCode="DEST",
        TransactionType=transaction_type,
        TransactionLines=lines,
        UserTranId=user_tran_id,
        Discount=discount,
    )

    return data


def get_checkout_lines_data(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    config: AvataxConfiguration,
    discounted: bool = False,
    discounts=None,
) -> List[TransactionLine]:
    data: List[TransactionLine] = []
    channel = checkout_info.channel
    tax_included = Site.objects.get_current().settings.include_taxes_in_prices
    shipping_address = checkout_info.shipping_address
    if shipping_address is None:
        raise TaxError("Shipping address required for ATE tax calculation")
    for sequence_number, line_info in enumerate(lines_info):
        prices_data = base_calculations.calculate_base_line_total_price(
            line_info, channel, discounts
        )

        # plugin requires int as invoice number - the line id was used for that
        # as order line id changes to `uuid` cannot be used anymore
        # the index of element + 1 in queryset is used instead;
        # the index value is increased be 1, as the line id 0 is
        # reserved for shipping
        append_line_to_data(
            amount=prices_data.amount,
            data=data,
            line_id=sequence_number + 1,
            quantity=line_info.line.quantity,
            shipping_address=shipping_address,
            tax_included=tax_included,
            variant=line_info.variant,
            variant_channel_listing=line_info.channel_listing,
            channel=channel,
            discounted=discounted,
            product_type=line_info.product_type,
        )

    delivery_method = checkout_info.delivery_method_info.delivery_method
    if delivery_method:
        price = getattr(delivery_method, "price", None)
        append_shipping_to_data(
            data,
            config.shipping_product_code,
            shipping_address,
            price.amount if price else None,
        )
    return data


def generate_request_data_from_checkout(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    config: AvataxConfiguration,
    transaction_token=None,
    transaction_type=TRANSACTION_TYPE,
    discounts=None,
):
    discount_amount = Decimal(checkout_info.checkout.discount_amount)
    invoice_number = None
    user_tran_id = None
    discounted = True if discount_amount > 0 else False

    lines = get_checkout_lines_data(
        checkout_info,
        lines_info,
        config,
        discounts=discounts,
        discounted=discounted,
    )
    # if there is no lines to sent we do not want to send the request to avalara
    if not lines:
        return {}

    data = generate_request_data(
        transaction_type,
        lines=lines,
        invoice_number=invoice_number,
        user_tran_id=user_tran_id,
        discount=discount_amount,
    )
    return data


def get_order_lines_data(
    order: "Order", discounted: bool = False, discounts=None
) -> List[TransactionLine]:

    data: List[TransactionLine] = []

    lines = order.lines.order_by("created_at").prefetch_related(
        "variant__channel_listings", "variant__product__product_type"
    )

    tax_included = Site.objects.get_current().settings.include_taxes_in_prices
    shipping_address = order.shipping_address
    if shipping_address is None:
        raise TaxError("Shipping address required for ATE tax calculation")

    for sequence_number, line in enumerate(lines):
        variant = line.variant
        if variant is None:
            continue

        variant_channel_listing = line.variant.channel_listings.get(  # type: ignore
            channel_id=order.channel_id
        )

        # plugin requires int as invoice number - the line id was used for that
        # as order line id changes to `uuid` cannot be used anymore
        # the index of element in queryset is used instead
        append_line_to_data(
            data=data,
            line_id=sequence_number,
            quantity=line.quantity,
            amount=line.unit_price_net_amount * line.quantity,
            tax_included=tax_included,
            variant=variant,
            shipping_address=shipping_address,
            variant_channel_listing=variant_channel_listing,
            channel=order.channel,
            discounted=discounted,
        )
    return data


def _fetch_new_taxes_data(
    data: Dict[str, Dict], data_cache_key: str, config: AvataxConfiguration
):
    transaction_url = urljoin(
        get_api_url(config.use_sandbox), "AvaTaxExcise/transactions/create"
    )
    with opentracing.global_tracer().start_active_span(
        "avatax_excise.transactions.create"
    ) as scope:
        span = scope.span
        span.set_tag(opentracing.tags.COMPONENT, "tax")
        span.set_tag("service.name", "avatax_excise")
        response = api_post_request(transaction_url, data, config)
    if response and response.get("Status") == "Success":
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

    Return cached response if requests data are the same.
    Fetch new data in other cases.
    """
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
    discounts,
    config: AvataxConfiguration,
) -> Dict[str, Any]:
    data = generate_request_data_from_checkout(
        checkout_info, lines_info, config, discounts=discounts
    )
    return get_cached_response_or_fetch(data, str(checkout_info.checkout.token), config)


def get_order_request_data(order: "Order", config=AvataxConfiguration):
    discount_total = get_total_order_discount(order)
    discounted = True if discount_total.amount > 0 else False

    lines = get_order_lines_data(order, discounted=discounted)
    # if there is no lines to sent we do not want to send the request to avalara
    if not lines:
        return {}
    data = generate_request_data(
        transaction_type=TRANSACTION_TYPE,
        lines=lines,
        invoice_number=f"{order.number}",
        discount=discount_total.amount,
    )
    return data


def get_order_tax_data(
    order: "Order", config: AvataxConfiguration, force_refresh=False
) -> Dict[str, Any]:
    data = get_order_request_data(order)

    response = get_cached_response_or_fetch(
        data, "order_%s" % order.id, config, force_refresh
    )
    if response and response.get("Status") != "Success":
        transaction_errors = response.get("TransactionErrors")
        customer_msg = ""
        if isinstance(transaction_errors, list):
            for error in transaction_errors:
                error_message = error.get("ErrorMessage")
                if error_message:
                    customer_msg += error_message
                error_code = response.get("ErrorCode", "")
                logger.warning(
                    "Unable to calculate taxes for order %s, error_code: %s, "
                    "error_msg: %s",
                    order.id,
                    error_code,
                    error_message,
                )
                if error_code == "-1003":
                    raise ValidationError(error_message)
        raise TaxError(customer_msg)
    return response


def metadata_requires_update(
    metadata: Dict[str, Dict],
    token_in_cache: str,
):
    """Check if Checkout metadata needs to be reset."""

    cached_data = cache.get(token_in_cache)
    if not cached_data or cached_data != metadata:
        return True
    return False


def build_metadata(taxes_data: Dict[str, Dict]):
    """Build the tax related metadata, add extra fields that we need as well."""
    return {
        get_metadata_key("itemized_taxes"): json.dumps(
            taxes_data.get("TransactionTaxes")
        ),
        get_metadata_key("tax_transaction"): json.dumps(taxes_data.get("Transaction")),
        get_metadata_key("sales_tax"): get_sales_tax(taxes_data),
        get_metadata_key("other_tax"): get_other_tax(taxes_data),
    }


def process_checkout_metadata(
    taxes_data: Dict[str, Dict],
    checkout: "Checkout",
    force_refresh: bool = False,
    cache_time: int = CACHE_TIME,
):
    """Process and store response from excise API in cache and metadata."""
    metadata_key = get_metadata_key("checkout_metadata_")
    data_cache_key = f"{metadata_key}{checkout.token}"

    metadata = build_metadata(taxes_data)

    if force_refresh or metadata_requires_update(metadata, data_cache_key):
        checkout.refresh_from_db(fields=["metadata"])
        checkout.store_value_in_metadata(items=metadata)
        checkout.save()
        cache.set(data_cache_key, metadata, cache_time)


def get_sales_tax(taxes_data: Dict[str, Dict]) -> int:
    """Build the sales tax amount where tax type is either SALES_TAX or USE_TAX."""
    return sum(
        map(
            lambda tax_data: tax_data.get("TaxAmount", 0),
            filter(
                lambda tax_data: tax_data.get("TaxType") == SALES_TAX
                or tax_data.get("TaxType") == USE_TAX,
                taxes_data.get("TransactionTaxes", []),
            ),
        )
    )


def get_other_tax(taxes_data: Dict[str, Dict]) -> int:
    """Build the remaining tax amount after getting the total sales tax.

    I.e. where the tax type is neither SALES_TAX nor USE_TAX.
    """
    return sum(
        map(
            lambda tax_data: tax_data.get("TaxAmount", 0),
            filter(
                lambda tax_data: tax_data.get("TaxType") != SALES_TAX
                and tax_data.get("TaxType") != USE_TAX,
                taxes_data.get("TransactionTaxes", []),
            ),
        )
    )
