from prices import TaxedMoneyRange

from ...core.utils import ZERO_TAXED_MONEY


class CostsData:
    __slots__ = ('costs', 'margins')

    def __init__(self, costs, margins):
        self.costs = sorted(costs, key=lambda x: x.gross)
        self.margins = sorted(margins)


def get_product_costs_data(product):
    purchase_costs_range = TaxedMoneyRange(
        start=ZERO_TAXED_MONEY, stop=ZERO_TAXED_MONEY)
    gross_margin = (0, 0)

    if not product.variants.exists():
        return purchase_costs_range, gross_margin

    variants = product.variants.all()
    costs_data = get_cost_data_from_variants(variants)

    if costs_data.costs:
        purchase_costs_range = TaxedMoneyRange(
            min(costs_data.costs), max(costs_data.costs))
    if costs_data.margins:
        gross_margin = (costs_data.margins[0], costs_data.margins[-1])
    return purchase_costs_range, gross_margin


def get_cost_data_from_variants(variants):
    costs = []
    margins = []
    for variant in variants:
        costs_data = get_variant_costs_data(variant)
        costs += costs_data.costs
        margins += costs_data.margins
    return CostsData(costs, margins)


def get_variant_costs_data(variant):
    costs = []
    margins = []
    for stock in variant.stock.all():
        costs.append(get_cost_price(stock))
        margin = get_margin_for_variant(stock)
        if margin:
            margins.append(margin)
    return CostsData(costs, margins)


def get_cost_price(stock):
    if not stock.cost_price:
        return ZERO_TAXED_MONEY
    return stock.get_total()


def get_margin_for_variant(stock):
    stock_price = stock.get_total()
    if stock_price is None:
        return None
    price = stock.variant.get_price_per_item()
    margin = price - stock_price
    percent = round((margin.gross / price.gross) * 100, 0)
    return percent
