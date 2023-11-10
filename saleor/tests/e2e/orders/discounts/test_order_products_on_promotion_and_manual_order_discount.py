import pytest

from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shop.utils.preparing_shop import prepare_shop
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
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        result_warehouse_id,
        result_channel_id,
        _,
        result_shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        result_warehouse_id,
        result_channel_id,
        variant_price=20,
    )

    promotion_name = "Percentage promotion"
    discount_value = 10
    discount_type = "PERCENTAGE"
    promotion_rule_name = "rule for product"

    promotion_data = create_promotion(e2e_staff_api_client, promotion_name)
    promotion_id = promotion_data["id"]

    catalogue_predicate = {"productPredicate": {"ids": [product_id]}}

    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        catalogue_predicate,
        discount_type,
        discount_value,
        promotion_rule_name,
        result_channel_id,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == result_channel_id
    assert product_predicate[0] == product_id

    # Step 1 - Create a draft order for a product with fixed promotion
    input = {
        "channelId": result_channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": result_shipping_method_id,
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
    promotion_value = round(float(product_variant_price) * discount_value / 100, 2)
    assert order_product_variant_id == product_variant_id
    unit_price = float(product_variant_price) - promotion_value
    undiscounted_unit_price = order_lines["order"]["lines"][0]["undiscountedUnitPrice"][
        "gross"
    ]["amount"]
    assert undiscounted_unit_price == float(product_variant_price)
    assert (
        order_lines["order"]["lines"][0]["unitPrice"]["gross"]["amount"] == unit_price
    )
    promotion_reason = order_lines["order"]["lines"][0]["unitDiscountReason"]
    assert promotion_reason == f"Promotion: {promotion_id}"

    # Step 3 - Add manual discount to the order
    manual_discount_input = {
        "valueType": "FIXED",
        "value": 2,
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
    discount_value = discount["value"]
    assert discount_value == 2

    # Step 4 - Add a shipping method to the order
    input = {"shippingMethod": result_shipping_method_id}
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
    product_price = order_line["undiscountedUnitPrice"]["gross"]["amount"]
    assert product_price == float(product_variant_price)
    assert promotion_value == order_line["unitDiscount"]["amount"]
    assert order_line["unitDiscountType"] == "FIXED"
    assert order_line["unitDiscountValue"] == promotion_value
    assert order_line["unitDiscountReason"] == promotion_reason
    product_discounted_price = product_price - promotion_value
    shipping_amount = order["order"]["shippingPrice"]["gross"]["amount"]
    assert shipping_amount == shipping_price
    subtotal = quantity * product_discounted_price - discount_value
    assert subtotal == order["order"]["subtotal"]["gross"]["amount"]
    assert subtotal == subtotal_gross_amount
    total = shipping_amount + subtotal
    assert total == order["order"]["total"]["gross"]["amount"]
    assert total == total_gross_amount
    assert order["order"]["status"] == "UNFULFILLED"
