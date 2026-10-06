from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ...discount.models import PromotionRule
from ...discount.utils.buyer_promotions import (
    calculate_best_discounted_price_for_rules,
)
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


@dataclass(frozen=True)
class ListingPrices:
    """The prices of a variant channel listing resolved for one buyer."""

    undiscounted: Money
    discounted: Money
    prior: Money | None


def get_listing_prices(
    variant_channel_listing: ProductVariantChannelListing,
    *,
    scoped_price: Money | None = None,
    promotion_rules: Iterable[PromotionRule] = (),
) -> ListingPrices | None:
    """Return the listing prices for a buyer, or `None` when the listing has no price.

    Without a scoped price and without promotion rules the stored discounted
    price is used. Otherwise the best of the rules is applied on the scoped
    price, or on the listing price when there is none.
    """
    if variant_channel_listing.price is None:
        return None
    rules = list(promotion_rules)
    if scoped_price is None and not rules:
        undiscounted = variant_channel_listing.price
        discounted = variant_channel_listing.discounted_price
        if discounted is None:
            discounted = undiscounted
    else:
        undiscounted = (
            scoped_price if scoped_price is not None else variant_channel_listing.price
        )
        discounted = calculate_best_discounted_price_for_rules(
            price=undiscounted,
            rules=rules,
            currency=variant_channel_listing.currency,
        )
    return ListingPrices(
        undiscounted=undiscounted,
        discounted=discounted,
        prior=variant_channel_listing.prior_price,
    )


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


def get_product_price_range(prices: Iterable[Money | None]) -> MoneyRange | None:
    """Return the range of the given variant prices, ignoring missing ones."""
    present_prices = [price for price in prices if price is not None]
    if present_prices:
        return MoneyRange(min(present_prices), max(present_prices))
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
    prices: Iterable[Money | None],
    tax_rate: Decimal,
    tax_calculation_strategy: str,
    prices_entered_with_tax: bool,
) -> TaxedMoneyRange | None:
    price: TaxedMoneyRange | None = None
    price_net_range = get_product_price_range(prices)
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
    scoped_prices: Mapping[int, Money] | None = None,
    promotion_rules_by_listing_id: Mapping[int, list[PromotionRule]] | None = None,
) -> ProductAvailability:
    """Return the product price ranges for a buyer.

    `scoped_prices` and `promotion_rules_by_listing_id` are keyed by the variant
    channel listing id. A listing without a scoped price uses its stored prices.
    """
    scoped_prices = scoped_prices or {}
    promotion_rules_by_listing_id = promotion_rules_by_listing_id or {}
    listings_prices = []
    for variant_channel_listing in variants_channel_listing:
        listing_prices = get_listing_prices(
            variant_channel_listing,
            scoped_price=scoped_prices.get(variant_channel_listing.pk),
            promotion_rules=promotion_rules_by_listing_id.get(
                variant_channel_listing.pk, []
            ),
        )
        if listing_prices is not None:
            listings_prices.append(listing_prices)

    undiscounted: TaxedMoneyRange | None = _calculate_product_price_with_taxes_range(
        [listing_prices.undiscounted for listing_prices in listings_prices],
        tax_rate,
        tax_calculation_strategy,
        prices_entered_with_tax,
    )

    discounted: TaxedMoneyRange | None = None
    prior: TaxedMoneyRange | None = None

    if undiscounted is not None:
        discounted = _calculate_product_price_with_taxes_range(
            [listing_prices.discounted for listing_prices in listings_prices],
            tax_rate,
            tax_calculation_strategy,
            prices_entered_with_tax,
        )

        prior = _calculate_product_price_with_taxes_range(
            [listing_prices.prior for listing_prices in listings_prices],
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
    scoped_price: Money | None = None,
    promotion_rules: Iterable[PromotionRule] = (),
) -> VariantAvailability | None:
    """Return the variant prices for a buyer, or `None` when the listing has no price.

    With a scoped price the promotion rules are re-applied on it. Without one the
    stored prices of the listing are used.
    """
    listing_prices = get_listing_prices(
        variant_channel_listing,
        scoped_price=scoped_price,
        promotion_rules=promotion_rules,
    )
    if listing_prices is None:
        return None
    discounted_price_taxed = _calculate_product_price_with_taxes(
        listing_prices.discounted,
        tax_rate,
        tax_calculation_strategy,
        prices_entered_with_tax,
    )
    undiscounted_price_taxed = _calculate_product_price_with_taxes(
        listing_prices.undiscounted,
        tax_rate,
        tax_calculation_strategy,
        prices_entered_with_tax,
    )
    prior_price = listing_prices.prior
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
