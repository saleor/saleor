from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

from prices import MoneyRange

from ...core.taxes import zero_money
from ..models import ProductChannelListing, ProductVariantChannelListing

if TYPE_CHECKING:
    from prices import Money


@dataclass
class CostsData:
    costs: List["Money"]
    margins: List[float]

    def __post_init__(self):
        self.costs = sorted(self.costs)
        self.margins = sorted(self.margins)


def get_product_costs_data(
    product_channel_listing: "ProductChannelListing", channel_slug,
) -> Tuple[MoneyRange, Tuple[float, float]]:

    purchase_costs_range = MoneyRange(start=zero_money(), stop=zero_money())
    margin = (0.0, 0.0)

    product = product_channel_listing.product
    if not product.variants.exists():
        return purchase_costs_range, margin

    variants = product.variants.all().values_list("id", flat=True)
    channel_listing = ProductVariantChannelListing.objects.filter(
        variant_id__in=variants, channel__slug=channel_slug
    )
    costs_data = get_cost_data_from_variant_channel_listing(channel_listing)
    if costs_data.costs:
        purchase_costs_range = MoneyRange(min(costs_data.costs), max(costs_data.costs))
    if costs_data.margins:
        margin = (costs_data.margins[0], costs_data.margins[-1])
    return purchase_costs_range, margin


def get_cost_data_from_variant_channel_listing(
    variant_channel_listings: Iterable["ProductVariantChannelListing"],
) -> CostsData:
    costs: List[CostsData] = []
    margins: List[float] = []
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
    margin = get_margin_for_variant(variant_channel_listing)
    if margin:
        margins.append(margin)
    return CostsData(costs, margins)


def get_cost_price(variant: "ProductVariantChannelListing") -> "Money":
    if not variant.cost_price:
        return zero_money()
    return variant.cost_price


def get_margin_for_variant(variant: "ProductVariantChannelListing") -> Optional[float]:
    if variant.cost_price is None:
        return None
    base_price = variant.price  # type: ignore
    if not base_price:
        return None
    margin = base_price - variant.cost_price
    percent = round((margin / base_price) * 100, 0)
    return percent
