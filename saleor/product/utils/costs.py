from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

from prices import MoneyRange

from ...core.taxes import zero_money

if TYPE_CHECKING:
    from prices import Money
    from ..models import Product, ProductVariant


@dataclass
class CostsData:
    costs: List["Money"]
    margins: List[float]

    def __post_init__(self):
        self.costs = sorted(self.costs)
        self.margins = sorted(self.margins)


def get_product_costs_data(
    product: "Product",
) -> Tuple[MoneyRange, Tuple[float, float]]:

    purchase_costs_range = MoneyRange(start=zero_money(), stop=zero_money())
    margin = (0.0, 0.0)

    if not product.variants.exists():
        return purchase_costs_range, margin

    variants = product.variants.all()
    costs_data = get_cost_data_from_variants(variants)
    if costs_data.costs:
        purchase_costs_range = MoneyRange(min(costs_data.costs), max(costs_data.costs))
    if costs_data.margins:
        margin = (costs_data.margins[0], costs_data.margins[-1])
    return purchase_costs_range, margin


def get_cost_data_from_variants(variants: Iterable["ProductVariant"]) -> CostsData:
    costs: List[CostsData] = []
    margins: List[float] = []
    for variant in variants:
        costs_data = get_variant_costs_data(variant)
        costs += costs_data.costs
        margins += costs_data.margins
    return CostsData(costs, margins)


def get_variant_costs_data(variant: "ProductVariant") -> CostsData:
    costs = []
    margins = []
    costs.append(get_cost_price(variant))
    margin = get_margin_for_variant(variant)
    if margin:
        margins.append(margin)
    return CostsData(costs, margins)


def get_cost_price(variant: "ProductVariant") -> "Money":
    if not variant.cost_price:
        return zero_money()
    return variant.cost_price


def get_margin_for_variant(variant: "ProductVariant") -> Optional[float]:
    if variant.cost_price is None:
        return None
    base_price = variant.base_price
    if not base_price:
        return None
    margin = base_price - variant.cost_price
    percent = round((margin / base_price) * 100, 0)
    return percent
