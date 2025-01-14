from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from prices import MoneyRange

from ...core.taxes import zero_money
from ..models import ProductVariantChannelListing

if TYPE_CHECKING:
    from prices import Money


@dataclass
class CostsData:
    costs: list["Money"]
    margins: list[float]

    def __post_init__(self):
        self.costs = sorted(self.costs)
        self.margins = sorted(self.margins)


def get_product_costs_data(
    variant_channel_listings: Iterable[ProductVariantChannelListing],
    has_variants: bool,
    currency: str,
) -> tuple[MoneyRange, tuple[float, float]]:
    purchase_costs_range = MoneyRange(
        start=zero_money(currency), stop=zero_money(currency)
    )
    margin = (0.0, 0.0)

    if not has_variants:
        return purchase_costs_range, margin

    costs_data = get_cost_data_from_variant_channel_listing(variant_channel_listings)
    if costs_data.costs:
        purchase_costs_range = MoneyRange(min(costs_data.costs), max(costs_data.costs))
    if costs_data.margins:
        margin = (costs_data.margins[0], costs_data.margins[-1])
    return purchase_costs_range, margin


def get_cost_data_from_variant_channel_listing(
    variant_channel_listings: Iterable["ProductVariantChannelListing"],
) -> CostsData:
    costs: list[CostsData] = []
    margins: list[float] = []
    for variant_channel_listing in variant_channel_listings:
        costs_data = get_variant_costs_data(variant_channel_listing)
        costs += costs_data.costs
        margins += costs_data.margins
    return CostsData(costs, margins)


def get_variant_costs_data(
    variant_channel_listing: "ProductVariantChannelListing",
) -> CostsData:
    costs = []
    margins = []
    costs.append(get_cost_price(variant_channel_listing))
    margin = get_margin_for_variant_channel_listing(variant_channel_listing)
    if margin:
        margins.append(margin)
    return CostsData(costs, margins)


def get_cost_price(variant_channel_listing: "ProductVariantChannelListing") -> "Money":
    if not variant_channel_listing.cost_price:
        return zero_money(variant_channel_listing.currency)
    return variant_channel_listing.cost_price


def get_margin_for_variant_channel_listing(
    variant_channel_listing: "ProductVariantChannelListing",
) -> float | None:
    if variant_channel_listing.cost_price is None:
        return None
    base_price = variant_channel_listing.price
    if not base_price:
        return None
    margin = base_price - variant_channel_listing.cost_price
    percent = round((margin / base_price) * 100, 0)
    return percent
