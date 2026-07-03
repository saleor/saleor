from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ...product.models import ProductChannelListing, ProductVariantChannelListing
from ...tax import TaxCalculationStrategy
from ...tax.calculations import calculate_flat_rate_tax


@dataclass
class ProductAvailability:
    on_sale: bool
    price_range: TaxedMoneyRange | None
    price_range_undiscounted: TaxedMoneyRange | None
    price_range_prior: TaxedMoneyRange | None
    discount: TaxedMoney | None
    discount_prior: TaxedMoney | None


@dataclass
class VariantAvailability:
    on_sale: bool
    price: TaxedMoney
    price_undiscounted: TaxedMoney
    price_prior: TaxedMoney | None
    discount: TaxedMoney | None
    discount_prior: TaxedMoney | None


def _get_total_discount_from_range(
    undiscounted: TaxedMoneyRange, discounted: TaxedMoneyRange
) -> TaxedMoney | None:
    """Calculate the discount amount between two TaxedMoneyRange.

    Subtract two prices and return their total discount, if any.
    Otherwise, it returns None.
    """
    return _get_total_discount(undiscounted.start, discounted.start)


def _get_total_discount(
    undiscounted: TaxedMoney, discounted: TaxedMoney
) -> TaxedMoney | None:
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
    field: Literal["price", "discounted_price", "prior_price"],
) -> MoneyRange | None:
    """Return the range of product prices based on product variants prices.

    When discounted parameter is True, the range of discounted prices is provided.
    """
    prices = []
    for channel_listing in variants_channel_listing:
        price: Money | None = channel_listing.__getattribute__(field)
        if price is not None:
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
    return TaxedMoney(price, price)


def _calculate_product_price_with_taxes_range(
    field: Literal["price", "discounted_price", "prior_price"],
    variants_channel_listing: list[ProductVariantChannelListing],
    tax_rate: Decimal,
    tax_calculation_strategy: str,
    prices_entered_with_tax: bool,
) -> TaxedMoneyRange | None:
    price: TaxedMoneyRange | None = None
    price_net_range = get_product_price_range(
        variants_channel_listing=variants_channel_listing, field=field
    )
    if price_net_range is not None:
        price = TaxedMoneyRange(
            start=_calculate_product_price_with_taxes(
                price_net_range.start,
                tax_rate,
                tax_calculation_strategy,
                prices_entered_with_tax,
            ),
            stop=_calculate_product_price_with_taxes(
                price_net_range.stop,
                tax_rate,
                tax_calculation_strategy,
                prices_entered_with_tax,
            ),
        )

    return price


def get_product_availability(
    *,
    product_channel_listing: ProductChannelListing | None,
    variants_channel_listing: list[ProductVariantChannelListing],
    prices_entered_with_tax: bool,
    tax_calculation_strategy: str,
    tax_rate: Decimal,
) -> ProductAvailability:
    undiscounted: TaxedMoneyRange | None = _calculate_product_price_with_taxes_range(
        "price",
        variants_channel_listing,
        tax_rate,
        tax_calculation_strategy,
        prices_entered_with_tax,
    )

    discounted: TaxedMoneyRange | None = None
    prior: TaxedMoneyRange | None = None

    if undiscounted is not None:
        discounted = _calculate_product_price_with_taxes_range(
            "discounted_price",
            variants_channel_listing,
            tax_rate,
            tax_calculation_strategy,
            prices_entered_with_tax,
        )

        prior = _calculate_product_price_with_taxes_range(
            "prior_price",
            variants_channel_listing,
            tax_rate,
            tax_calculation_strategy,
            prices_entered_with_tax,
        )

    discount = None
    if undiscounted is not None and discounted is not None:
        discount = _get_total_discount_from_range(undiscounted, discounted)

    discount_prior = None
    if prior is not None and discounted is not None:
        discount_prior = _get_total_discount_from_range(prior, discounted)

    is_visible = (
        product_channel_listing is not None and product_channel_listing.is_visible
    )
    is_on_sale = is_visible and discount is not None

    return ProductAvailability(
        on_sale=is_on_sale,
        price_range=discounted,
        price_range_undiscounted=undiscounted,
        price_range_prior=prior,
        discount=discount,
        discount_prior=discount_prior,
    )


def get_variant_availability(
    *,
    variant_channel_listing: ProductVariantChannelListing,
    product_channel_listing: ProductChannelListing | None,
    prices_entered_with_tax: bool,
    tax_calculation_strategy: str,
    tax_rate: Decimal,
) -> VariantAvailability | None:
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
    prior_price = variant_channel_listing.prior_price
    prior_price_taxed = None
    if prior_price is not None:
        prior_price_taxed = _calculate_product_price_with_taxes(
            prior_price,
            tax_rate,
            tax_calculation_strategy,
            prices_entered_with_tax,
        )
    discount = _get_total_discount(undiscounted_price_taxed, discounted_price_taxed)

    discount_prior = None
    if prior_price_taxed is not None:
        discount_prior = _get_total_discount(prior_price_taxed, discounted_price_taxed)

    is_visible = (
        product_channel_listing is not None and product_channel_listing.is_visible
    )
    is_on_sale = is_visible and discount is not None

    return VariantAvailability(
        on_sale=is_on_sale,
        price=discounted_price_taxed,
        price_undiscounted=undiscounted_price_taxed,
        price_prior=prior_price_taxed,
        discount=discount,
        discount_prior=discount_prior,
    )
