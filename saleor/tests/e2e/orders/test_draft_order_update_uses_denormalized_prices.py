from decimal import Decimal

import pytest

from ....core.prices import quantize_price
from ....discount.models import PromotionRule
from ....product.models import Product
from ....product.utils.variant_prices import update_discounted_prices_for_promotion
from ....product.utils.variants import fetch_variants_for_promotion_rules
from .. import DEFAULT_ADDRESS
from ..product.utils import create_product_variant_channel_listing
from ..product.utils.preparing_product import prepare_product
from ..promotions.utils import (
    create_promotion,
    create_promotion_rule,
    update_promotion_rule,
)
from ..shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
)
from ..shop.utils import prepare_shop
from ..taxes.utils import update_country_tax_rates
from ..utils import assign_permissions
from .utils import (
    draft_order_create,
    draft_order_update,
    order_line_delete,
    order_lines_create,
)


@pytest.mark.e2e
def test_draft_order_update_uses_denormalized_prices_CORE_0251(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "prices_entered_with_tax": False,
    }
    initial_shipping_price = Decimal(10)
    currency = "USD"
    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "Inpost",
                                "add_channels": {"price": initial_shipping_price},
                            }
                        ],
                    },
                ],
                "order_settings": {
                    "includeDraftOrderInVoucherUsage": True,
                },
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_zone_id = shop_data[0]["shipping_zones"][0]["id"]
    initial_shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][
        0
    ]["id"]

    tax_rate = Decimal("1.1")
    update_country_tax_rates(
        e2e_staff_api_client,
        "US",
        [{"rate": (tax_rate - 1) * 100}],
    )

    (
        product_id,
        variant_id,
        initial_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=Decimal(20)
    )
    initial_variant_price = Decimal(initial_variant_price)

    promotion_name = "Promotion Fixed"
    initial_discount_reward = Decimal(5)
    discount_type = "FIXED"
    promotion_rule_name = "rule for product"
    promotion_type = "CATALOGUE"

    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type
    )
    promotion_id = promotion_data["id"]

    catalogue_predicate = {"productPredicate": {"ids": [product_id]}}
    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
        "cataloguePredicate": catalogue_predicate,
        "rewardValue": initial_discount_reward,
        "rewardValueType": discount_type,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    promotion_rule_id = promotion_rule["id"]

    # update prices
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    update_discounted_prices_for_promotion(Product.objects.all())

    # Step 1 - Create a draft order for a product with fixed promotion
    initial_quantity = Decimal(2)
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": initial_shipping_method_id,
        "lines": [{"variantId": variant_id, "quantity": initial_quantity}],
    }
    data = draft_order_create(e2e_staff_api_client, input)

    undisocunted_unit_price = initial_variant_price
    unit_price = undisocunted_unit_price - initial_discount_reward
    undiscounted_line_total = quantize_price(
        undisocunted_unit_price * initial_quantity, currency
    )
    line_total = quantize_price(unit_price * initial_quantity, currency)
    undiscounted_total = undiscounted_line_total + initial_shipping_price
    total = line_total + initial_shipping_price

    order_data = data["order"]
    order_id = order_data["id"]
    assert not order_data["discounts"]
    assert order_data["shippingPrice"]["net"]["amount"] == initial_shipping_price
    assert order_data["shippingPrice"]["gross"]["amount"] == quantize_price(
        initial_shipping_price * tax_rate, currency
    )
    assert order_data["total"]["net"]["amount"] == total
    assert order_data["total"]["gross"]["amount"] == quantize_price(
        total * tax_rate, currency
    )
    assert order_data["undiscountedTotal"]["net"]["amount"] == undiscounted_total
    assert order_data["undiscountedTotal"]["gross"]["amount"] == quantize_price(
        undiscounted_total * tax_rate, currency
    )

    assert len(order_data["lines"]) == 1
    line_data = order_data["lines"][0]
    line_id = line_data["id"]
    assert line_data["unitPrice"]["net"]["amount"] == unit_price
    assert line_data["unitPrice"]["gross"]["amount"] == quantize_price(
        unit_price * tax_rate, currency
    )
    assert (
        line_data["undiscountedUnitPrice"]["net"]["amount"] == undisocunted_unit_price
    )
    assert line_data["undiscountedUnitPrice"]["gross"]["amount"] == quantize_price(
        undisocunted_unit_price * tax_rate, currency
    )
    assert line_data["totalPrice"]["net"]["amount"] == line_total
    assert line_data["totalPrice"]["gross"]["amount"] == quantize_price(
        line_total * tax_rate, currency
    )
    assert (
        line_data["undiscountedTotalPrice"]["net"]["amount"] == undiscounted_line_total
    )
    assert line_data["undiscountedTotalPrice"]["gross"]["amount"] == quantize_price(
        undiscounted_line_total * tax_rate, currency
    )
    assert line_data["unitDiscount"]["amount"] == initial_discount_reward
    assert line_data["unitDiscountReason"] == f"Promotion: {promotion_id}"

    # Step 2 - Update channel listing for variant
    new_variant_price = initial_variant_price - Decimal(2)
    data = create_product_variant_channel_listing(
        e2e_staff_api_client, variant_id, channel_id, new_variant_price
    )
    assert data["channelListings"][0]["price"]["amount"] != initial_variant_price
    assert data["channelListings"][0]["channel"]["id"] == channel_id

    # Step 3 - Update promotion rule reward
    new_discount_reward = Decimal(7)
    input = {"rewardValue": new_discount_reward}
    update_promotion_rule(e2e_staff_api_client, promotion_rule_id, input)

    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    update_discounted_prices_for_promotion(Product.objects.all())

    # Step 4 - Create new shipping method
    data = create_shipping_method(e2e_staff_api_client, shipping_zone_id)
    new_shipping_method_id = data["id"]

    # Step 5 - Update new shipping method price
    new_shipping_price = Decimal(15)
    data = create_shipping_method_channel_listing(
        e2e_staff_api_client,
        new_shipping_method_id,
        channel_id,
        {"price": new_shipping_price},
    )
    assert data["channelListings"][0]["price"]["amount"] == new_shipping_price

    # Step 6 - Update order shipping method what leads to price recalculation.
    # Base variant prices shouldn't be updated
    data = draft_order_update(
        e2e_staff_api_client, order_id, {"shippingMethod": new_shipping_method_id}
    )
    undisocunted_unit_price = initial_variant_price
    unit_price = undisocunted_unit_price - initial_discount_reward
    undiscounted_line_total = quantize_price(
        undisocunted_unit_price * initial_quantity, currency
    )
    line_total = quantize_price(unit_price * initial_quantity, currency)
    undiscounted_total = undiscounted_line_total + new_shipping_price
    total = line_total + new_shipping_price

    order_data = data["order"]
    assert not order_data["discounts"]
    assert order_data["shippingPrice"]["net"]["amount"] == new_shipping_price
    assert order_data["shippingPrice"]["gross"]["amount"] == quantize_price(
        new_shipping_price * tax_rate, currency
    )
    assert order_data["total"]["net"]["amount"] == total
    assert order_data["total"]["gross"]["amount"] == quantize_price(
        total * tax_rate, currency
    )
    assert order_data["undiscountedTotal"]["net"]["amount"] == undiscounted_total
    assert order_data["undiscountedTotal"]["gross"]["amount"] == quantize_price(
        undiscounted_total * tax_rate, currency
    )

    assert len(order_data["lines"]) == 1
    line_data = order_data["lines"][0]
    assert line_data["unitPrice"]["net"]["amount"] == unit_price
    assert line_data["unitPrice"]["gross"]["amount"] == quantize_price(
        unit_price * tax_rate, currency
    )
    assert (
        line_data["undiscountedUnitPrice"]["net"]["amount"] == undisocunted_unit_price
    )
    assert line_data["undiscountedUnitPrice"]["gross"]["amount"] == quantize_price(
        undisocunted_unit_price * tax_rate, currency
    )
    assert line_data["totalPrice"]["net"]["amount"] == line_total
    assert line_data["totalPrice"]["gross"]["amount"] == quantize_price(
        line_total * tax_rate, currency
    )
    assert (
        line_data["undiscountedTotalPrice"]["net"]["amount"] == undiscounted_line_total
    )
    assert line_data["undiscountedTotalPrice"]["gross"]["amount"] == quantize_price(
        undiscounted_line_total * tax_rate, currency
    )
    assert line_data["unitDiscount"]["amount"] == initial_discount_reward
    assert line_data["unitDiscountReason"] == f"Promotion: {promotion_id}"

    # Step 7 - Delete the order line
    data = order_line_delete(e2e_staff_api_client, line_id)

    undiscounted_total = new_shipping_price
    total = new_shipping_price

    order_data = data["order"]
    assert order_data["shippingPrice"]["net"]["amount"] == new_shipping_price
    assert order_data["shippingPrice"]["gross"]["amount"] == quantize_price(
        new_shipping_price * tax_rate, currency
    )
    assert order_data["total"]["net"]["amount"] == total
    assert order_data["total"]["gross"]["amount"] == quantize_price(
        total * tax_rate, currency
    )
    assert order_data["undiscountedTotal"]["net"]["amount"] == undiscounted_total
    assert order_data["undiscountedTotal"]["gross"]["amount"] == quantize_price(
        undiscounted_total * tax_rate, currency
    )
    assert not order_data["lines"]

    # Step 8 - Add the order line again. Prices should be taken from current
    # channel listing values
    new_quantity = 3
    lines = [
        {"variantId": variant_id, "quantity": new_quantity},
    ]
    data = order_lines_create(e2e_staff_api_client, order_id, lines)

    undisocunted_unit_price = new_variant_price
    unit_price = undisocunted_unit_price - new_discount_reward
    undiscounted_line_total = quantize_price(
        undisocunted_unit_price * new_quantity, currency
    )
    line_total = quantize_price(unit_price * new_quantity, currency)
    undiscounted_total = undiscounted_line_total + new_shipping_price
    total = line_total + new_shipping_price

    order_data = data["order"]
    assert not order_data["discounts"]
    assert order_data["shippingPrice"]["net"]["amount"] == new_shipping_price
    assert order_data["shippingPrice"]["gross"]["amount"] == quantize_price(
        new_shipping_price * tax_rate, currency
    )
    assert order_data["total"]["net"]["amount"] == total
    assert Decimal(str(order_data["total"]["gross"]["amount"])) == quantize_price(
        total * tax_rate, currency
    )
    assert order_data["undiscountedTotal"]["net"]["amount"] == undiscounted_total
    assert Decimal(
        str(order_data["undiscountedTotal"]["gross"]["amount"])
    ) == quantize_price(undiscounted_total * tax_rate, currency)

    assert len(order_data["lines"]) == 1
    line_data = order_data["lines"][0]
    assert line_data["unitPrice"]["net"]["amount"] == unit_price
    assert Decimal(str(line_data["unitPrice"]["gross"]["amount"])) == quantize_price(
        unit_price * tax_rate, currency
    )
    assert (
        line_data["undiscountedUnitPrice"]["net"]["amount"] == undisocunted_unit_price
    )
    assert Decimal(
        str(line_data["undiscountedUnitPrice"]["gross"]["amount"])
    ) == quantize_price(undisocunted_unit_price * tax_rate, currency)
    assert line_data["totalPrice"]["net"]["amount"] == line_total
    assert Decimal(str(line_data["totalPrice"]["gross"]["amount"])) == quantize_price(
        line_total * tax_rate, currency
    )
    assert (
        line_data["undiscountedTotalPrice"]["net"]["amount"] == undiscounted_line_total
    )
    assert Decimal(
        str(line_data["undiscountedTotalPrice"]["gross"]["amount"])
    ) == quantize_price(undiscounted_line_total * tax_rate, currency)
    assert line_data["unitDiscount"]["amount"] == new_discount_reward
    assert line_data["unitDiscountReason"] == f"Promotion: {promotion_id}"
