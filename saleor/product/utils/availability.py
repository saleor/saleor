from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, Union

import opentracing
from django.conf import settings
from django_countries.fields import Country
from prices import MoneyRange, TaxedMoney, TaxedMoneyRange

from ...channel.models import Channel
from ...core.utils import to_local_currency
from ...discount import DiscountInfo
from ...discount.utils import calculate_discounted_price
from ...product.models import (
    Collection,
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)

if TYPE_CHECKING:
    # flake8: noqa
    from ...plugins.manager import PluginsManager


@dataclass
class ProductAvailability:
    on_sale: bool
    price_range: Optional[TaxedMoneyRange]
    price_range_undiscounted: Optional[TaxedMoneyRange]
    discount: Optional[TaxedMoney]
    price_range_local_currency: Optional[TaxedMoneyRange]
    discount_local_currency: Optional[TaxedMoneyRange]


@dataclass
class VariantAvailability:
    on_sale: bool
    price: TaxedMoney
    price_undiscounted: TaxedMoney
    discount: Optional[TaxedMoney]
    price_local_currency: Optional[TaxedMoney]
    discount_local_currency: Optional[TaxedMoney]


def _get_total_discount_from_range(
    undiscounted: TaxedMoneyRange, discounted: TaxedMoneyRange
) -> Optional[TaxedMoney]:
    """Calculate the discount amount between two TaxedMoneyRange.

    Subtract two prices and return their total discount, if any.
    Otherwise, it returns None.
    """
    return _get_total_discount(undiscounted.start, discounted.start)


def _get_total_discount(
    undiscounted: TaxedMoney, discounted: TaxedMoney
) -> Optional[TaxedMoney]:
    """Calculate the discount amount between two TaxedMoney.

    Subtract two prices and return their total discount, if any.
    Otherwise, it returns None.
    """
    if undiscounted > discounted:
        return undiscounted - discounted
    return None


def _get_product_price_range(
    discounted: Union[MoneyRange, TaxedMoneyRange],
    undiscounted: Union[MoneyRange, TaxedMoneyRange],
    local_currency: Optional[str] = None,
) -> Tuple[TaxedMoneyRange, TaxedMoney]:
    price_range_local = None
    discount_local_currency = None

    if local_currency:
        price_range_local = to_local_currency(discounted, local_currency)
        undiscounted_local = to_local_currency(undiscounted, local_currency)
        if undiscounted_local and undiscounted_local.start > price_range_local.start:
            discount_local_currency = undiscounted_local.start - price_range_local.start

    return price_range_local, discount_local_currency


def get_variant_price(
    *,
    variant: ProductVariant,
    variant_channel_listing: ProductVariantChannelListing,
    product: Product,
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
    channel: Channel
):
    return calculate_discounted_price(
        product=product,
        price=variant_channel_listing.price,
        collections=collections,
        discounts=discounts,
        channel=channel,
        variant_id=variant.id,
    )


def get_product_price_range(
    *,
    product: Product,
    variants: Iterable[ProductVariant],
    variants_channel_listing: List[ProductVariantChannelListing],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
    channel: Channel,
) -> Optional[MoneyRange]:
    if variants:
        variants_channel_listing_dict = {
            channel_listing.variant_id: channel_listing
            for channel_listing in variants_channel_listing
            if channel_listing
        }
        prices = []
        for variant in variants:
            variant_channel_listing = variants_channel_listing_dict.get(variant.id)
            if variant_channel_listing:
                price = get_variant_price(
                    variant=variant,
                    variant_channel_listing=variant_channel_listing,
                    product=product,
                    collections=collections,
                    discounts=discounts,
                    channel=channel,
                )
                prices.append(price)
        if prices:
            return MoneyRange(min(prices), max(prices))

    return None


def get_product_availability(
    *,
    product: Product,
    product_channel_listing: Optional[ProductChannelListing],
    variants: Iterable[ProductVariant],
    variants_channel_listing: List[ProductVariantChannelListing],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
    channel: Channel,
    manager: "PluginsManager",
    country: Country,
    local_currency: Optional[str] = None,
) -> ProductAvailability:
    channel_slug = channel.slug

    discounted = None
    discounted_net_range = get_product_price_range(
        product=product,
        variants=variants,
        variants_channel_listing=variants_channel_listing,
        collections=collections,
        discounts=discounts,
        channel=channel,
    )
    if discounted_net_range is not None:
        discounted = TaxedMoneyRange(
            start=manager.apply_taxes_to_product(
                product,
                discounted_net_range.start,
                country,
                channel_slug=channel_slug,
            ),
            stop=manager.apply_taxes_to_product(
                product,
                discounted_net_range.stop,
                country,
                channel_slug=channel_slug,
            ),
        )

    undiscounted = None
    undiscounted_net_range = get_product_price_range(
        product=product,
        variants=variants,
        variants_channel_listing=variants_channel_listing,
        collections=collections,
        discounts=[],
        channel=channel,
    )
    if undiscounted_net_range is not None:
        undiscounted = TaxedMoneyRange(
            start=manager.apply_taxes_to_product(
                product,
                undiscounted_net_range.start,
                country,
                channel_slug=channel_slug,
            ),
            stop=manager.apply_taxes_to_product(
                product,
                undiscounted_net_range.stop,
                country,
                channel_slug=channel_slug,
            ),
        )

    discount = None
    price_range_local = None
    discount_local_currency = None
    if undiscounted_net_range is not None and discounted_net_range is not None:
        discount = _get_total_discount_from_range(undiscounted, discounted)
        price_range_local, discount_local_currency = _get_product_price_range(
            discounted, undiscounted, local_currency
        )

    is_visible = (
        product_channel_listing is not None and product_channel_listing.is_visible
    )
    is_on_sale = is_visible and discount is not None

    return ProductAvailability(
        on_sale=is_on_sale,
        price_range=discounted,
        price_range_undiscounted=undiscounted,
        discount=discount,
        price_range_local_currency=price_range_local,
        discount_local_currency=discount_local_currency,
    )


def get_variant_availability(
    variant: ProductVariant,
    variant_channel_listing: ProductVariantChannelListing,
    product: Product,
    product_channel_listing: Optional[ProductChannelListing],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
    channel: Channel,
    plugins: "PluginsManager",
    country: Country,
    local_currency: Optional[str] = None,
) -> VariantAvailability:
    with opentracing.global_tracer().start_active_span("get_variant_availability"):
        channel_slug = channel.slug
        discounted = plugins.apply_taxes_to_product(
            product,
            get_variant_price(
                variant=variant,
                variant_channel_listing=variant_channel_listing,
                product=product,
                collections=collections,
                discounts=discounts,
                channel=channel,
            ),
            country,
            channel_slug=channel_slug,
        )
        undiscounted = plugins.apply_taxes_to_product(
            product,
            get_variant_price(
                variant=variant,
                variant_channel_listing=variant_channel_listing,
                product=product,
                collections=collections,
                discounts=[],
                channel=channel,
            ),
            country,
            channel_slug=channel_slug,
        )

        discount = _get_total_discount(undiscounted, discounted)

        if local_currency:
            price_local_currency = to_local_currency(discounted, local_currency)
            discount_local_currency = to_local_currency(discount, local_currency)
        else:
            price_local_currency = None
            discount_local_currency = None

        is_visible = (
            product_channel_listing is not None and product_channel_listing.is_visible
        )
        is_on_sale = is_visible and discount is not None

        return VariantAvailability(
            on_sale=is_on_sale,
            price=discounted,
            price_undiscounted=undiscounted,
            discount=discount,
            price_local_currency=price_local_currency,
            discount_local_currency=discount_local_currency,
        )
