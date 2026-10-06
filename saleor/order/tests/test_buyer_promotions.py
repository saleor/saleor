from decimal import Decimal

from prices import Money

from ...graphql.order.utils import OrderLineData
from ...product.models import Product
from ...product.utils.variant_prices import update_discounted_prices_for_promotion
from ..fetch import fetch_draft_order_lines_info
from ..utils import attach_buyer_pricing_to_lines_data, create_order_line


def _store_guest_price(product):
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))


def test_attach_buyer_pricing_to_lines_data_picks_the_buyer_rule(
    draft_order,
    variant,
    product,
    b2b_customer_user,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    _store_guest_price(product)
    order = draft_order
    order.user = b2b_customer_user
    order.save(update_fields=["user"])
    line_data = OrderLineData(variant=variant, quantity=1)

    # when
    attach_buyer_pricing_to_lines_data(order, [line_data])

    # then
    [rule_info] = line_data.rules_info
    assert rule_info.rule == promotion_rule_for_customer_type
    assert rule_info.resolved_for_buyer is True
    assert line_data.scoped_price is None


def test_attach_buyer_pricing_to_lines_data_ignores_buyer_rules_without_user(
    draft_order, variant, product, catalogue_promotion, promotion_rule_for_customer_type
):
    # given
    _store_guest_price(product)
    order = draft_order
    order.user = None
    order.save(update_fields=["user"])
    line_data = OrderLineData(variant=variant, quantity=1)

    # when
    attach_buyer_pricing_to_lines_data(order, [line_data])

    # then
    assert line_data.rules_info is None


def test_create_order_line_applies_the_buyer_rule(
    draft_order,
    variant,
    product,
    b2b_customer_user,
    site_settings,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    _store_guest_price(product)
    order = draft_order
    order.user = b2b_customer_user
    order.save(update_fields=["user"])
    quantity = 2
    line_data = OrderLineData(variant=variant, quantity=quantity)
    attach_buyer_pricing_to_lines_data(order, [line_data])
    currency = order.currency

    # when
    line = create_order_line(order, line_data, None, site_settings)

    # then
    assert line.undiscounted_base_unit_price == Money(Decimal(10), currency)
    assert line.base_unit_price == Money(Decimal("7.50"), currency)
    discount = line.discounts.get()
    assert discount.promotion_rule == promotion_rule_for_customer_type
    assert discount.amount == Money(Decimal("2.50") * quantity, currency)


def test_fetch_draft_order_lines_info_picks_the_buyer_rule(
    draft_order,
    variant,
    product,
    b2b_customer_user,
    site_settings,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    _store_guest_price(product)
    order = draft_order
    line = create_order_line(
        order, OrderLineData(variant=variant, quantity=1), None, site_settings
    )
    order.user = b2b_customer_user
    order.save(update_fields=["user"])

    # when
    lines_info = fetch_draft_order_lines_info(order, fetch_actual_prices=True)

    # then
    line_info = next(info for info in lines_info if info.line.pk == line.pk)
    [rule_info] = line_info.rules_info
    assert rule_info.rule == promotion_rule_for_customer_type
    assert rule_info.resolved_for_buyer is True
