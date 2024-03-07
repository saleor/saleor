import pytest

from .....product.tasks import recalculate_discounted_price_for_products_task
from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...product.utils.product_query import get_product
from ...promotions.utils import (
    create_promotion,
    create_promotion_rule,
    delete_promotion,
    promotion_query,
)
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
)


@pytest.mark.e2e
def test_order_promotion_still_applied_to_the_order_when_promotion_is_removed_CORE_2115(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    promotion_name = "Promotion Fixed"
    discount_value = 5
    discount_type = "FIXED"
    promotion_rule_name = "rule for product"

    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=20
    )

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
        "rewardValue": discount_value,
        "rewardValueType": discount_type,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id

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
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_lines = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_product_variant_id = order_lines["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id == product_variant_id
    unit_price = float(product_variant_price) - float(discount_value)
    undiscounted_price = order_lines["order"]["lines"][0]["undiscountedUnitPrice"][
        "gross"
    ]["amount"]
    assert float(undiscounted_price) == float(product_variant_price)
    assert (
        order_lines["order"]["lines"][0]["unitPrice"]["gross"]["amount"] == unit_price
    )
    promotion_reason = order_lines["order"]["lines"][0]["unitDiscountReason"]
    assert promotion_reason == f"Promotion: {promotion_id}"

    # Step 3 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    draft_update = draft_order_update(e2e_staff_api_client, order_id, input)
    order_shipping_id = draft_update["order"]["deliveryMethod"]["id"]
    shipping_price = draft_update["order"]["shippingPrice"]["gross"]["amount"]
    subtotal_gross_amount = draft_update["order"]["subtotal"]["gross"]["amount"]
    total_gross_amount = draft_update["order"]["total"]["gross"]["amount"]
    assert order_shipping_id is not None

    # Step 4 - Remove the promotion and check the product is not on promotion
    delete_promotion(e2e_staff_api_client, promotion_id)

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    data = promotion_query(e2e_staff_api_client, promotion_id)
    assert data["promotion"] is None
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    assert product_data["id"] == product_id
    assert product_data["pricing"]["onSale"] is False
    variant_data = product_data["variants"][0]
    variant_id = product_data["variants"][0]["id"]
    assert variant_id == product_variant_id
    assert variant_data["pricing"]["onSale"] is False

    # Step 5 - Complete order and check the sale is still applied
    order = draft_order_complete(e2e_staff_api_client, order_id)
    order_complete_id = order["order"]["id"]
    assert order_complete_id == order_id
    order_line = order["order"]["lines"][0]
    assert order_line["productVariantId"] == product_variant_id
    assert order_line["unitDiscount"]["amount"] == float(discount_value)
    assert order_line["unitDiscountType"] == discount_type
    assert order_line["unitDiscountValue"] == float(discount_value)
    assert order_line["unitDiscountReason"] == promotion_reason
    product_price = order_line["undiscountedUnitPrice"]["gross"]["amount"]
    assert product_price == float(undiscounted_price)
    assert product_price == float(product_variant_price)
    shipping_amount = order["order"]["shippingPrice"]["gross"]["amount"]
    assert shipping_amount == shipping_price
    subtotal = product_price - order_line["unitDiscountValue"]
    assert subtotal == order["order"]["subtotal"]["gross"]["amount"]
    assert subtotal == subtotal_gross_amount
    total = shipping_amount + subtotal
    assert total == order["order"]["total"]["gross"]["amount"]
    assert total == float(total_gross_amount)

    assert order["order"]["status"] == "UNFULFILLED"
