from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional, Tuple, Union

from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

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
from ...tax import TaxCalculationStrategy
from ...tax.calculations import calculate_flat_rate_tax


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


def _calculate_product_price_with_taxes(
    price: Money,
    tax_rate: Decimal,
    tax_calculation_strategy: str,
    prices_entered_with_tax: bool,
):
    # Currently only FLAT_RATES strategy allows calculating taxes for product types;
    # support for apps will be added in the future.
    if tax_calculation_strategy == TaxCalculationStrategy.FLAT_RATES:
        return calculate_flat_rate_tax(price, tax_rate, prices_entered_with_tax)
    else:
        return TaxedMoney(price, price)


def get_product_availability(
    *,
    product: Product,
    product_channel_listing: Optional[ProductChannelListing],
    variants: Iterable[ProductVariant],
    variants_channel_listing: List[ProductVariantChannelListing],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
    channel: Channel,
    local_currency: Optional[str] = None,
    prices_entered_with_tax: bool,
    tax_calculation_strategy: str,
    tax_rate: Decimal
) -> ProductAvailability:
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
            start=_calculate_product_price_with_taxes(
                discounted_net_range.start,
                tax_rate,
                tax_calculation_strategy,
                prices_entered_with_tax,
            ),
            stop=_calculate_product_price_with_taxes(
                discounted_net_range.stop,
                tax_rate,
                tax_calculation_strategy,
                prices_entered_with_tax,
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
            start=_calculate_product_price_with_taxes(
                undiscounted_net_range.start,
                tax_rate,
                tax_calculation_strategy,
                prices_entered_with_tax,
            ),
            stop=_calculate_product_price_with_taxes(
                undiscounted_net_range.stop,
                tax_rate,
                tax_calculation_strategy,
                prices_entered_with_tax,
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
    *,
    variant: ProductVariant,
    variant_channel_listing: ProductVariantChannelListing,
    product: Product,
    product_channel_listing: Optional[ProductChannelListing],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
    channel: Channel,
    local_currency: Optional[str] = None,
    prices_entered_with_tax: bool,
    tax_calculation_strategy: str,
    tax_rate: Decimal
) -> VariantAvailability:
    discounted_price = get_variant_price(
        variant=variant,
        variant_channel_listing=variant_channel_listing,
        product=product,
        collections=collections,
        discounts=discounts,
        channel=channel,
    )
    discounted_price_taxed = _calculate_product_price_with_taxes(
        discounted_price,
        tax_rate,
        tax_calculation_strategy,
        prices_entered_with_tax,
    )
    undiscounted_price = get_variant_price(
        variant=variant,
        variant_channel_listing=variant_channel_listing,
        product=product,
        collections=collections,
        discounts=[],
        channel=channel,
    )
    undiscounted_price_taxed = _calculate_product_price_with_taxes(
        undiscounted_price,
        tax_rate,
        tax_calculation_strategy,
        prices_entered_with_tax,
    )
    discount = _get_total_discount(undiscounted_price_taxed, discounted_price_taxed)

    if local_currency:
        price_local_currency = to_local_currency(discounted_price_taxed, local_currency)
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
        price=discounted_price_taxed,
        price_undiscounted=undiscounted_price_taxed,
        discount=discount,
        price_local_currency=price_local_currency,
        discount_local_currency=discount_local_currency,
    )
