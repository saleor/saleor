from dataclasses import dataclass
from functools import singledispatch
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple

from django.utils.encoding import smart_text
from django.utils.functional import SimpleLazyObject

from ..discount import DiscountInfo, VoucherType
from ..discount.utils import fetch_active_discounts
from ..graphql.shipping.utils import annotate_active_shipping_methods
from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethodChannelListing
from ..shipping.utils import convert_to_shipping_method_data

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..discount.models import Voucher
    from ..plugins.manager import PluginsManager
    from ..product.models import (
        Collection,
        Product,
        ProductChannelListing,
        ProductType,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from .models import Checkout, CheckoutLine


@dataclass
class CheckoutLineInfo:
    line: "CheckoutLine"
    variant: "ProductVariant"
    channel_listing: "ProductVariantChannelListing"
    product: "Product"
    product_type: "ProductType"
    collections: List["Collection"]
    voucher: Optional["Voucher"] = None


@dataclass
class CheckoutInfo:
    checkout: "Checkout"
    user: Optional["User"]
    channel: "Channel"
    billing_address: Optional["Address"]
    shipping_address: Optional["Address"]
    delivery_method_info: "DeliveryMethodBase"
    all_shipping_methods: List["ShippingMethodData"]

    def get_country(self) -> str:
        address = self.shipping_address or self.billing_address
        if address is None or not address.country:
            return self.checkout.country.code
        return address.country.code

    def get_customer_email(self) -> str:
        return self.user.email if self.user else self.checkout.email

    @property
    def valid_shipping_methods(self) -> List["ShippingMethodData"]:
        return [method for method in self.all_shipping_methods if method.active]


@dataclass(frozen=True)
class DeliveryMethodBase:
    delivery_method: Optional["ShippingMethodData"] = None
    shipping_address: Optional["Address"] = None

    @property
    def delivery_method_order_field(self) -> dict:
        return {"shipping_method": self.delivery_method}

    @property
    def delivery_method_name(self) -> Dict[str, Optional[str]]:
        return {"shipping_method_name": None}

    def is_method_in_valid_methods(self, checkout_info: "CheckoutInfo") -> bool:
        return False


@dataclass(frozen=True)
class ShippingMethodInfo(DeliveryMethodBase):
    delivery_method: "ShippingMethodData"
    shipping_address: Optional["Address"]

    @property
    def delivery_method_name(self) -> Dict[str, Optional[str]]:
        return {"shipping_method_name": smart_text(self.delivery_method.name)}

    @property
    def delivery_method_order_field(self) -> dict:
        return {"shipping_method_id": self.delivery_method.id}

    def is_method_in_valid_methods(self, checkout_info: "CheckoutInfo") -> bool:
        valid_delivery_methods = checkout_info.valid_shipping_methods
        return bool(
            valid_delivery_methods and self.delivery_method in valid_delivery_methods
        )


def fetch_checkout_lines(
    checkout: "Checkout",
) -> Tuple[Iterable[CheckoutLineInfo], Iterable[int]]:
    """Fetch checkout lines as CheckoutLineInfo objects."""

    from .utils import get_voucher_for_checkout

    lines = checkout.lines.prefetch_related(
        "variant__product__collections",
        "variant__product__channel_listings__channel",
        "variant__channel_listings__channel",
        "variant__product__product_type",
    )
    lines_info = []
    unavailable_variant_pks = []
    product_channel_listing_mapping: Dict[int, Optional["ProductChannelListing"]] = {}

    for line in lines:
        variant = line.variant
        product = variant.product
        product_type = product.product_type
        collections = list(product.collections.all())

        variant_channel_listing = _get_variant_channel_listing(
            variant, checkout.channel_id
        )

        if not _is_variant_valid(
            checkout, product, variant_channel_listing, product_channel_listing_mapping
        ):
            unavailable_variant_pks.append(variant.pk)
            continue

        lines_info.append(
            CheckoutLineInfo(
                line=line,
                variant=variant,
                channel_listing=variant_channel_listing,
                product=product,
                product_type=product_type,
                collections=collections,
            )
        )

    if checkout.voucher_code and lines_info:
        channel_slug = checkout.channel.slug
        voucher = get_voucher_for_checkout(
            checkout, channel_slug=channel_slug, with_prefetch=True
        )
        if not voucher:
            # in case when voucher is expired, it will be null so no need to apply any
            # discount from voucher
            return lines_info, unavailable_variant_pks
        if voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order:
            _apply_voucher_on_product(voucher, checkout, lines_info)
    return lines_info, unavailable_variant_pks


def _get_variant_channel_listing(variant: "ProductVariant", channel_id: int):
    variant_channel_listing = None
    for channel_listing in variant.channel_listings.all():
        if channel_listing.channel_id == channel_id:
            variant_channel_listing = channel_listing
    return variant_channel_listing


def _is_variant_valid(
    checkout: "Checkout",
    product: "Product",
    variant_channel_listing: "ProductVariantChannelListing",
    product_channel_listing_mapping: dict,
):
    if not variant_channel_listing or variant_channel_listing.price is None:
        return False

    product_channel_listing = _get_product_channel_listing(
        product_channel_listing_mapping, checkout.channel_id, product
    )

    if (
        not product_channel_listing
        or product_channel_listing.is_available_for_purchase() is False
    ):
        return False

    return True


def _get_product_channel_listing(
    product_channel_listing_mapping: dict, channel_id: int, product: "Product"
):
    product_channel_listing = product_channel_listing_mapping.get(product.id)
    if product.id not in product_channel_listing_mapping:
        for channel_listing in product.channel_listings.all():  # type: ignore
            if channel_listing.channel_id == channel_id:
                product_channel_listing = channel_listing
        product_channel_listing_mapping[product.id] = product_channel_listing
    return product_channel_listing


def _apply_voucher_on_product(
    voucher: "Voucher", checkout: "Checkout", lines_info: Iterable[CheckoutLineInfo]
):
    from .utils import get_discounted_lines

    discounted_lines_by_voucher: List[CheckoutLineInfo] = []
    if voucher.apply_once_per_order:
        discounts = fetch_active_discounts()
        channel = checkout.channel
        cheapest_line_price = None
        cheapest_line = None
        for line_info in lines_info:
            line_price = line_info.variant.get_price(
                product=line_info.product,
                collections=line_info.collections,
                channel=channel,
                channel_listing=line_info.channel_listing,
                discounts=discounts,
            )
            if not cheapest_line or cheapest_line_price > line_price:
                cheapest_line_price = line_price
                cheapest_line = line_info
        if cheapest_line:
            discounted_lines_by_voucher.append(cheapest_line)
    else:
        discounted_lines_by_voucher.extend(get_discounted_lines(lines_info, voucher))
    for line_info in lines_info:
        if line_info in discounted_lines_by_voucher:
            line_info.voucher = voucher


@singledispatch
def get_delivery_method_info(
    delivery_method: Optional["ShippingMethodData"],
    address=Optional["Address"],
) -> DeliveryMethodBase:
    if delivery_method is None:
        return DeliveryMethodBase()
    if isinstance(delivery_method, ShippingMethodData):
        return ShippingMethodInfo(delivery_method, address)

    raise NotImplementedError()


def fetch_checkout_info(
    checkout: "Checkout",
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
) -> CheckoutInfo:
    """Fetch checkout as CheckoutInfo object."""

    channel = checkout.channel
    shipping_address = checkout.shipping_address
    shipping_method = checkout.shipping_method
    shipping_method_channel_listing = None
    all_shipping_method_channel_listings = list(
        ShippingMethodChannelListing.objects.filter(
            channel=channel,
        )
    )
    if shipping_method:
        for listing in all_shipping_method_channel_listings:
            if listing.shipping_method_id == shipping_method.id:
                shipping_method_channel_listing = listing
                break

        shipping_method = convert_to_shipping_method_data(
            shipping_method,
            shipping_method_channel_listing,  # type: ignore
        )

    delivery_method_info = get_delivery_method_info(shipping_method, shipping_address)

    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        delivery_method_info=delivery_method_info,
        all_shipping_methods=[],
    )
    checkout_info.all_shipping_methods = SimpleLazyObject(
        lambda: get_shipping_method_list_for_checkout_info(
            checkout_info,
            shipping_address,
            lines,
            discounts,
            manager,
            all_shipping_method_channel_listings,
        )
    )  # type: ignore
    return checkout_info


def update_checkout_info_shipping_address(
    checkout_info: CheckoutInfo,
    address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
):
    checkout_info.shipping_address = address
    valid_methods = get_shipping_method_list_for_checkout_info(
        checkout_info,
        address,
        lines,
        discounts,
        manager,
        checkout_info.channel.shipping_method_listings.all(),
    )
    checkout_info.all_shipping_methods = valid_methods


def get_valid_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable[ShippingMethodChannelListing],
) -> List["ShippingMethodData"]:
    from .utils import get_valid_shipping_methods_for_checkout

    country_code = shipping_address.country.code if shipping_address else None
    subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, discounts
    )
    subtotal -= checkout_info.checkout.discount
    valid_shipping_methods = get_valid_shipping_methods_for_checkout(
        checkout_info,
        lines,
        subtotal,
        shipping_channel_listings,
        country_code=country_code,
    )

    return valid_shipping_methods


def get_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable[ShippingMethodChannelListing],
):
    """Return a list of shipping methods for checkout info.

    Shipping methods excluded by Saleor's own business logic are not present
    in the result list.

    Availability of shipping methods according to plugins is indicated
    by the `active` field.
    """
    methods = get_valid_shipping_method_list_for_checkout_info(
        checkout_info,
        shipping_address,
        lines,
        discounts,
        manager,
        shipping_channel_listings,
    )
    excluded_shipping_methods = manager.excluded_shipping_methods_for_checkout(
        checkout_info.checkout, methods
    )
    annotate_active_shipping_methods(
        methods,
        excluded_shipping_methods,
    )
    return methods
