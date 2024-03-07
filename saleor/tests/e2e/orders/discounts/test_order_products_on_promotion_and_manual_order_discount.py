from decimal import Decimal

import pytest

from .....core.prices import quantize_price
from .....product.tasks import recalculate_discounted_price_for_products_task
from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_discount_add,
    order_lines_create,
)


@pytest.mark.e2e
def test_order_products_on_promotion_and_manual_order_discount_CORE_2108(
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

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]
    base_shipping_price = 10
    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=20,
    )

    promotion_name = "Percentage promotion"
    promotion_discount_value = Decimal(10)
    discount_type = "PERCENTAGE"
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
        "rewardValue": promotion_discount_value,
        "rewardValueType": discount_type,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id
    currency = "USD"

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 1 - Create a draft order for a product with fixed promotion
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": shipping_method_id,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 2 - Add order lines to the order
    quantity = 2
    lines = [{"variantId": product_variant_id, "quantity": quantity}]
    order_lines = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_product_variant_id = order_lines["order"]["lines"][0]["variant"]["id"]
    product_variant_price = Decimal(product_variant_price)
    promotion_value = quantize_price(
        product_variant_price * promotion_discount_value / 100, currency
    )
    assert order_product_variant_id == product_variant_id
    unit_price = product_variant_price - promotion_value
    undiscounted_unit_price = order_lines["order"]["lines"][0]["undiscountedUnitPrice"][
        "gross"
    ]["amount"]
    assert undiscounted_unit_price == product_variant_price
    assert (
        order_lines["order"]["lines"][0]["unitPrice"]["gross"]["amount"] == unit_price
    )
    promotion_reason = order_lines["order"]["lines"][0]["unitDiscountReason"]
    assert promotion_reason == f"Promotion: {promotion_id}"
    subtotal = unit_price * quantity

    # Step 3 - Add manual discount to the order
    manual_discount_value = 2
    manual_discount_input = {
        "valueType": "FIXED",
        "value": manual_discount_value,
    }
    discount_data = order_discount_add(
        e2e_staff_api_client,
        order_id,
        manual_discount_input,
    )
    discount = discount_data["order"]["discounts"][0]
    assert discount is not None
    assert discount["type"] == "MANUAL"
    assert discount["valueType"] == "FIXED"
    assert discount["value"] == manual_discount_value

    # Step 4 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    draft_update = draft_order_update(e2e_staff_api_client, order_id, input)
    order_shipping_id = draft_update["order"]["deliveryMethod"]["id"]
    shipping_price = draft_update["order"]["shippingPrice"]["gross"]["amount"]
    subtotal_gross_amount = draft_update["order"]["subtotal"]["gross"]["amount"]
    total_gross_amount = draft_update["order"]["total"]["gross"]["amount"]
    assert order_shipping_id is not None

    # Step 5 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    order_complete_id = order["order"]["id"]
    assert order_complete_id == order_id
    order_line = order["order"]["lines"][0]
    assert order_line["productVariantId"] == product_variant_id
    product_price = quantize_price(
        Decimal(order_line["undiscountedUnitPrice"]["gross"]["amount"]), currency
    )
    manual_discount_subtotal_share = (
        subtotal / (base_shipping_price + subtotal) * manual_discount_value
    )
    manual_discount_shipping_share = (
        manual_discount_value - manual_discount_subtotal_share
    )
    assert product_price == product_variant_price
    assert order_line["unitDiscount"]["amount"] == promotion_value
    assert order_line["unitDiscountType"] == "PERCENTAGE"
    assert order_line["unitDiscountValue"] == promotion_discount_value
    assert order_line["unitDiscountReason"] == promotion_reason
    product_discounted_price = product_price - promotion_value
    shipping_amount = quantize_price(
        Decimal(order["order"]["shippingPrice"]["gross"]["amount"]), currency
    )
    assert shipping_amount == quantize_price(
        base_shipping_price - manual_discount_shipping_share, currency
    )
    assert float(shipping_amount) == shipping_price
    subtotal = quantize_price(
        quantity * product_discounted_price - manual_discount_subtotal_share, currency
    )
    assert float(subtotal) == order["order"]["subtotal"]["gross"]["amount"]
    assert float(subtotal) == subtotal_gross_amount
    total = shipping_amount + subtotal
    assert total == order["order"]["total"]["gross"]["amount"]
    assert total == total_gross_amount
    assert order["order"]["status"] == "UNFULFILLED"
