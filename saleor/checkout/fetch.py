from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional

from ..shipping.models import ShippingMethodChannelListing

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..discount import DiscountInfo
    from ..plugins.manager import PluginsManager
    from ..product.models import (
        Collection,
        Product,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from ..shipping.models import ShippingMethod
    from .models import Checkout, CheckoutLine


@dataclass
class CheckoutLineInfo:
    line: "CheckoutLine"
    variant: "ProductVariant"
    channel_listing: "ProductVariantChannelListing"
    product: "Product"
    collections: List["Collection"]


@dataclass
class CheckoutInfo:
    checkout: "Checkout"
    user: Optional["User"]
    channel: "Channel"
    billing_address: Optional["Address"]
    shipping_address: Optional["Address"]
    shipping_method: Optional["ShippingMethod"]
    valid_shipping_methods: List["ShippingMethod"]
    shipping_method_channel_listings: Optional[ShippingMethodChannelListing]

    def get_country(self) -> str:
        address = self.shipping_address or self.billing_address
        if address is None or not address.country:
            return self.checkout.country.code
        return address.country.code

    def get_customer_email(self) -> str:
        return self.user.email if self.user else self.checkout.email


def fetch_checkout_lines(checkout: "Checkout") -> Iterable[CheckoutLineInfo]:
    """Fetch checkout lines as CheckoutLineInfo objects."""
    lines = checkout.lines.prefetch_related(
        "variant__product__collections",
        "variant__channel_listings__channel",
        "variant__product__product_type",
    )
    lines_info = []

    for line in lines:
        variant = line.variant
        product = variant.product
        collections = list(product.collections.all())

        variant_channel_listing = None
        for channel_listing in line.variant.channel_listings.all():
            if channel_listing.channel_id == checkout.channel_id:
                variant_channel_listing = channel_listing

        # FIXME: Temporary solution to pass type checks. Figure out how to handle case
        # when variant channel listing is not defined for a checkout line.
        if not variant_channel_listing:
            continue

        lines_info.append(
            CheckoutLineInfo(
                line=line,
                variant=variant,
                channel_listing=variant_channel_listing,
                product=product,
                collections=collections,
            )
        )
    return lines_info


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
    shipping_channel_listings = ShippingMethodChannelListing.objects.filter(
        shipping_method=shipping_method, channel=channel
    ).first()
    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        shipping_method_channel_listings=shipping_channel_listings,
        valid_shipping_methods=[],
    )
    valid_shipping_methods = get_valid_shipping_method_list_for_checkout_info(
        checkout_info, shipping_address, lines, discounts, manager
    )
    checkout_info.valid_shipping_methods = valid_shipping_methods

    return checkout_info


def update_checkout_info_shipping_address(
    checkout_info: CheckoutInfo,
    address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
):
    checkout_info.shipping_address = address
    valid_methods = get_valid_shipping_method_list_for_checkout_info(
        checkout_info, address, lines, discounts, manager
    )
    checkout_info.valid_shipping_methods = valid_methods


def get_valid_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
):
    from .utils import get_valid_shipping_methods_for_checkout

    country_code = shipping_address.country.code if shipping_address else None
    subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, discounts
    )
    valid_shipping_method = get_valid_shipping_methods_for_checkout(
        checkout_info, lines, subtotal, country_code=country_code
    )
    valid_shipping_method = (
        list(valid_shipping_method) if valid_shipping_method is not None else []
    )
    return valid_shipping_method


def update_checkout_info_shipping_method(
    checkout_info: CheckoutInfo, shipping_method: Optional["ShippingMethod"]
):
    checkout_info.shipping_method = shipping_method
    checkout_info.shipping_method_channel_listings = (
        (
            ShippingMethodChannelListing.objects.filter(
                shipping_method=shipping_method, channel=checkout_info.channel
            ).first()
        )
        if shipping_method
        else None
    )
