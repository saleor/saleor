from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ...product.models import ProductChannelListing, ProductVariantChannelListing
from ...tax import TaxCalculationStrategy
from ...tax.calculations import calculate_flat_rate_tax


@dataclass
class ProductAvailability:
    on_sale: bool
    price_range: Optional[TaxedMoneyRange]
    price_range_undiscounted: Optional[TaxedMoneyRange]
    discount: Optional[TaxedMoney]


@dataclass
class VariantAvailability:
    on_sale: bool
    price: TaxedMoney
    price_undiscounted: TaxedMoney
    discount: Optional[TaxedMoney]


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


def get_product_price_range(
    *,
    variants_channel_listing: list[ProductVariantChannelListing],
    discounted: bool,
) -> Optional[MoneyRange]:
    """Return the range of product prices based on product variants prices.

    When discounted parameter is True, the range of discounted prices is provided.
    """
    prices = []
    for channel_listing in variants_channel_listing:
        if channel_listing.price:
            price = (
                channel_listing.discounted_price
                if discounted
                else channel_listing.price
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
    product_channel_listing: Optional[ProductChannelListing],
    variants_channel_listing: list[ProductVariantChannelListing],
    prices_entered_with_tax: bool,
    tax_calculation_strategy: str,
    tax_rate: Decimal,
) -> ProductAvailability:
    discounted: Optional[TaxedMoneyRange] = None
    discounted_net_range = get_product_price_range(
        variants_channel_listing=variants_channel_listing, discounted=True
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

    undiscounted: Optional[TaxedMoneyRange] = None
    undiscounted_net_range = get_product_price_range(
        variants_channel_listing=variants_channel_listing,
        discounted=False,
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
    if undiscounted is not None and discounted is not None:
        discount = _get_total_discount_from_range(undiscounted, discounted)

    is_visible = (
        product_channel_listing is not None and product_channel_listing.is_visible
    )
    is_on_sale = is_visible and discount is not None

    return ProductAvailability(
        on_sale=is_on_sale,
        price_range=discounted,
        price_range_undiscounted=undiscounted,
        discount=discount,
    )


def get_variant_availability(
    *,
    variant_channel_listing: ProductVariantChannelListing,
    product_channel_listing: Optional[ProductChannelListing],
    prices_entered_with_tax: bool,
    tax_calculation_strategy: str,
    tax_rate: Decimal,
) -> Optional[VariantAvailability]:
    if variant_channel_listing.price is None:
        return None
    discounted_price_taxed = _calculate_product_price_with_taxes(
        variant_channel_listing.discounted_price,
        tax_rate,
        tax_calculation_strategy,
        prices_entered_with_tax,
    )
    undiscounted_price = variant_channel_listing.price
    undiscounted_price_taxed = _calculate_product_price_with_taxes(
        undiscounted_price,
        tax_rate,
        tax_calculation_strategy,
        prices_entered_with_tax,
    )
    discount = _get_total_discount(undiscounted_price_taxed, discounted_price_taxed)

    is_visible = (
        product_channel_listing is not None and product_channel_listing.is_visible
    )
    is_on_sale = is_visible and discount is not None

    return VariantAvailability(
        on_sale=is_on_sale,
        price=discounted_price_taxed,
        price_undiscounted=undiscounted_price_taxed,
        discount=discount,
    )
