from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional

from django.utils.functional import SimpleLazyObject

from ..discount import DiscountInfo, VoucherType
from ..discount.utils import fetch_active_discounts
from ..graphql.shipping.utils import (
    annotate_active_shipping_methods,
    annotate_shipping_methods_with_price,
    convert_shipping_method_model_to_dataclass,
)
from ..shipping.models import ShippingMethodChannelListing

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..discount.models import Voucher
    from ..plugins.manager import PluginsManager
    from ..product.models import (
        Collection,
        Product,
        ProductType,
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

    from .utils import get_discounted_lines, get_voucher_for_checkout

    lines = checkout.lines.prefetch_related(
        "variant__product__collections",
        "variant__channel_listings__channel",
        "variant__product__product_type",
    )
    lines_info = []

    for line in lines:
        variant = line.variant
        product = variant.product
        product_type = product.product_type
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
            return lines_info
        if voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order:
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
                discounted_lines_by_voucher.extend(
                    get_discounted_lines(lines_info, voucher)
                )
            for line_info in lines_info:
                if line_info in discounted_lines_by_voucher:
                    line_info.voucher = voucher
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

    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        shipping_method_channel_listings=shipping_method_channel_listing,
        valid_shipping_methods=[],
    )
    checkout_info.valid_shipping_methods = SimpleLazyObject(
        lambda: get_valid_shipping_method_list_for_checkout_info(
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
    channel_listings: Optional[List["ShippingMethodChannelListing"]] = None,
):
    from .utils import get_valid_shipping_methods_for_checkout

    if channel_listings is None:
        channel_listings = list(
            ShippingMethodChannelListing.objects.filter(channel=checkout_info.channel)
        )

    country_code = shipping_address.country.code if shipping_address else None
    subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, discounts
    )
    subtotal -= checkout_info.checkout.discount
    checkout = checkout_info.checkout

    valid_shipping_methods = (
        get_valid_shipping_methods_for_checkout(
            checkout_info, lines, subtotal, country_code=country_code
        )
        or []
    )
    annotate_shipping_methods_with_price(
        valid_shipping_methods,
        channel_listings,
        checkout_info.shipping_address,
        checkout_info.channel.slug,
        manager,
    )
    shipping_method_dataclasses = [
        convert_shipping_method_model_to_dataclass(shipping)
        for shipping in valid_shipping_methods
    ]
    excluded_shipping_methods = manager.excluded_shipping_methods_for_checkout(
        checkout, shipping_method_dataclasses
    )
    annotate_active_shipping_methods(
        valid_shipping_methods,
        excluded_shipping_methods,
    )

    return [method for method in valid_shipping_methods if method.active]


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
