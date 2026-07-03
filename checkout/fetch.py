from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from functools import cached_property
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.conf import settings
from prices import Money

from ..core.prices import quantize_price
from ..core.pricing.interface import LineInfo
from ..core.taxes import zero_money
from ..discount import VoucherType
from ..discount.interface import (
    VariantPromotionRuleInfo,
    fetch_variant_rules_info,
    fetch_voucher_info,
)
from ..shipping.interface import ShippingMethodData
from ..shipping.utils import (
    convert_checkout_delivery_to_shipping_method_data,
)
from ..warehouse.models import Warehouse
from .delivery_context import (
    CollectionPointInfo,
    DeliveryMethodBase,
    ShippingMethodInfo,
    get_valid_collection_points_for_checkout,
)
from .models import Checkout, CheckoutLine

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..discount.models import (
        CheckoutDiscount,
        CheckoutLineDiscount,
        Voucher,
        VoucherCode,
    )
    from ..plugins.manager import PluginsManager
    from ..product.models import (
        Product,
        ProductChannelListing,
        ProductType,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from ..tax.models import TaxClass, TaxConfiguration


@dataclass
class CheckoutLineInfo(LineInfo):
    line: "CheckoutLine"
    variant: "ProductVariant"
    product: "Product"
    product_type: "ProductType"
    discounts: list["CheckoutLineDiscount"]
    rules_info: list["VariantPromotionRuleInfo"] = field(repr=False)
    channel_listing: Optional["ProductVariantChannelListing"] = field(repr=False)

    tax_class: Optional["TaxClass"] = field(default=None, repr=False)

    @cached_property
    def variant_discounted_price(self) -> Money:
        """Return the discounted variant price.

        `variant_discounted_price` means price with the most beneficial applicable
        catalogue promotion.
        If listing is present return the discounted price from the listing,
        if listing is not present, calculate current unit price based on
        `undiscounted_unit_price` and catalogue promotion discounts.
        """

        # if price_override is set, it takes precedence over any other price for
        # further calculations
        if self.line.price_override is not None:
            return Money(self.line.price_override, self.line.currency)

        if self.channel_listing and self.channel_listing.discounted_price is not None:
            return self.channel_listing.discounted_price

        catalogue_discounts = self.get_catalogue_discounts()
        total_price = self.undiscounted_unit_price * self.line.quantity
        for discount in catalogue_discounts:
            total_price -= discount.amount

        unit_price = max(
            total_price / self.line.quantity, zero_money(self.line.currency)
        )
        return quantize_price(unit_price, self.line.currency)

    @cached_property
    def undiscounted_unit_price(self) -> Money:
        """Provide undiscounted unit price.

        Return the undiscounted variant price when listing is present. If variant
        doesn't have listing, use denormalized price.
        """
        if self.channel_listing and self.channel_listing.price is not None:
            return self.variant.get_base_price(
                self.channel_listing, self.line.price_override
            )
        return self.line.undiscounted_unit_price

    @cached_property
    def prior_unit_price_amount(self) -> Decimal | None:
        """Provide prior unit price."""
        if self.channel_listing and self.channel_listing.price is not None:
            return self.variant.get_prior_price_amount(self.channel_listing)
        return self.line.prior_unit_price_amount


@dataclass
class CheckoutInfo:
    manager: "PluginsManager" = field(compare=False)
    checkout: "Checkout"
    user: Optional["User"]
    channel: "Channel"
    billing_address: Optional["Address"]
    shipping_address: Optional["Address"]
    tax_configuration: "TaxConfiguration"
    discounts: list["CheckoutDiscount"]
    lines: list[CheckoutLineInfo]
    collection_point: Optional["Warehouse"] = None
    voucher: Optional["Voucher"] = None
    voucher_code: Optional["VoucherCode"] = None
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME

    allow_sync_webhooks: bool = True

    @cached_property
    def valid_pick_up_points(self) -> Iterable["Warehouse"]:
        return list(
            get_valid_collection_points_for_checkout(
                self.lines, self.channel.id, quantity_check=False
            )
        )

    def get_delivery_method_info(self) -> DeliveryMethodBase:
        delivery_method: ShippingMethodData | Warehouse | None = None

        if assigned_sm := self.checkout.assigned_delivery:
            delivery_method = convert_checkout_delivery_to_shipping_method_data(
                assigned_sm
            )
            return ShippingMethodInfo(delivery_method, self.shipping_address)

        delivery_method = self.collection_point
        if delivery_method is not None:
            return CollectionPointInfo(delivery_method, delivery_method.address)

        return DeliveryMethodBase()

    def get_country(self) -> str:
        address = self.shipping_address or self.billing_address
        if address is None or not address.country:
            return self.checkout.country.code
        return address.country.code

    def get_customer_email(self) -> str | None:
        if self.checkout.email:
            return self.checkout.email
        if self.user:
            return self.user.email
        return None


def fetch_checkout_lines(
    checkout: "Checkout",
    prefetch_variant_attributes: bool = False,
    skip_lines_with_unavailable_variants: bool = True,
    skip_recalculation: bool = False,
    voucher: Optional["Voucher"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple[list[CheckoutLineInfo], list[int]]:
    """Fetch checkout lines as CheckoutLineInfo objects."""
    from ..discount.utils.voucher import attach_voucher_to_line_info
    from .utils import get_voucher_for_checkout

    select_related_fields = ["variant__product__product_type__tax_class"]
    prefetch_related_fields = [
        "variant__product__collections",
        "variant__product__channel_listings__channel",
        "variant__product__product_type__tax_class__country_rates",
        "variant__product__tax_class__country_rates",
        "variant__channel_listings__channel",
        "variant__channel_listings__variantlistingpromotionrule__promotion_rule__promotion__translations",
        "variant__channel_listings__variantlistingpromotionrule__promotion_rule__translations",
        "discounts__promotion_rule__promotion",
    ]
    if prefetch_variant_attributes:
        prefetch_related_fields.extend(
            [
                "variant__attributes__assignment__attribute",
                "variant__attributes__values",
            ]
        )
    lines = checkout.lines.select_related(*select_related_fields).prefetch_related(
        *prefetch_related_fields
    )
    lines_info = []
    unavailable_variant_pks = []
    product_channel_listing_mapping: dict[int, ProductChannelListing | None] = {}
    channel = checkout.channel

    for line in lines:
        variant = line.variant
        product = variant.product
        product_type = product.product_type
        collections = list(product.collections.all())
        discounts = list(line.discounts.all())

        variant_channel_listing = get_variant_channel_listing(
            variant, checkout.channel_id
        )
        translation_language_code = checkout.language_code
        rules_info = (
            fetch_variant_rules_info(variant_channel_listing, translation_language_code)
            if not line.is_gift
            else []
        )

        if not skip_recalculation and not _is_variant_valid(
            checkout, product, variant_channel_listing, product_channel_listing_mapping
        ):
            unavailable_variant_pks.append(variant.pk)
            lines_info.append(
                CheckoutLineInfo(
                    line=line,
                    variant=variant,
                    channel_listing=variant_channel_listing,
                    product=product,
                    product_type=product_type,
                    collections=collections,
                    tax_class=product.tax_class or product_type.tax_class,
                    discounts=discounts,
                    rules_info=rules_info,
                    channel=channel,
                    voucher=None,
                    voucher_code=None,
                )
            )
            continue

        lines_info.append(
            CheckoutLineInfo(
                line=line,
                variant=variant,
                channel_listing=variant_channel_listing,
                product=product,
                product_type=product_type,
                collections=collections,
                tax_class=product.tax_class or product_type.tax_class,
                discounts=discounts,
                rules_info=rules_info,
                channel=channel,
                voucher=None,
                voucher_code=None,
            )
        )

    if not skip_recalculation and checkout.voucher_code and lines_info:
        if not voucher:
            voucher, _ = get_voucher_for_checkout(
                checkout,
                channel_slug=channel.slug,
                with_prefetch=True,
                database_connection_name=database_connection_name,
            )
        if not voucher:
            # in case when voucher is expired, it will be null so no need to apply any
            # discount from voucher
            return lines_info, unavailable_variant_pks
        if voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order:
            voucher_info = fetch_voucher_info(voucher, checkout.voucher_code)
            attach_voucher_to_line_info(voucher_info, lines_info)
    return lines_info, unavailable_variant_pks


def get_variant_channel_listing(
    variant: "ProductVariant", channel_id: int
) -> Optional["ProductVariantChannelListing"]:
    variant_channel_listing = None
    for channel_listing in variant.channel_listings.all():
        if channel_listing.channel_id == channel_id:
            variant_channel_listing = channel_listing
    return variant_channel_listing


def _product_channel_listing_is_valid(
    checkout: "Checkout",
    product: "Product",
    product_channel_listing_mapping: dict,
):
    product_channel_listing = _get_product_channel_listing(
        product_channel_listing_mapping, checkout.channel_id, product
    )
    if (
        not product_channel_listing
        or product_channel_listing.is_available_for_purchase() is False
        or not product_channel_listing.is_visible
    ):
        return False
    return True


def _is_variant_valid(
    checkout: "Checkout",
    product: "Product",
    variant_channel_listing: Optional["ProductVariantChannelListing"],
    product_channel_listing_mapping: dict,
):
    if not variant_channel_listing or variant_channel_listing.price is None:
        return False

    if not _product_channel_listing_is_valid(
        checkout,
        product,
        product_channel_listing_mapping,
    ):
        return False
    return True


def _get_product_channel_listing(
    product_channel_listing_mapping: dict, channel_id: int, product: "Product"
):
    product_channel_listing = product_channel_listing_mapping.get(product.id)
    if product.id not in product_channel_listing_mapping:
        for channel_listing in product.channel_listings.all():
            if channel_listing.channel_id == channel_id:
                product_channel_listing = channel_listing
        product_channel_listing_mapping[product.id] = product_channel_listing
    return product_channel_listing


def fetch_checkout_info(
    checkout: "Checkout",
    lines: list[CheckoutLineInfo],
    manager: "PluginsManager",
    voucher: Optional["Voucher"] = None,
    voucher_code: Optional["VoucherCode"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> CheckoutInfo:
    """Fetch checkout as CheckoutInfo object."""
    from .utils import get_voucher_for_checkout

    channel = checkout.channel
    tax_configuration = channel.tax_configuration
    shipping_address = checkout.shipping_address

    if not voucher or not voucher_code:
        voucher, voucher_code = get_voucher_for_checkout(
            checkout,
            channel_slug=channel.slug,
            database_connection_name=database_connection_name,
        )

    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        tax_configuration=tax_configuration,
        discounts=list(checkout.discounts.all()),
        lines=lines,
        manager=manager,
        collection_point=checkout.collection_point,
        voucher=voucher,
        voucher_code=voucher_code,
        database_connection_name=database_connection_name,
    )
    return checkout_info


def find_checkout_line_info(
    lines: list["CheckoutLineInfo"],
    line_id: "UUID",
) -> "CheckoutLineInfo":
    """Return checkout line info from lines parameter.

    The return value represents the updated version of checkout_line_info parameter.
    """
    return next(line_info for line_info in lines if line_info.line.pk == line_id)
