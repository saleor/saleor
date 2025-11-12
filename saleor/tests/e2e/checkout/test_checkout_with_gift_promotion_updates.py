"""E2E test for gift promotion with discount price expiration.

This test verifies the complete flow of gift promotions with dynamic updates:
1. Create checkout with a product line
2. Create a gift promotion (order promotion with gift reward)
3. Update shipping - gift line should be added
4. Update gift promotion - change the gift variant
5. Update shipping again - gift line should update with new variant and prices
6. Complete checkout successfully
"""

import pytest

from ..product.utils.preparing_product import prepare_product
from ..promotions.utils.promotion_create import create_promotion
from ..promotions.utils.promotion_rule_create import create_promotion_rule
from ..promotions.utils.promotion_rule_update import update_promotion_rule
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_lines_add,
)


def get_checkout_with_lines(api_client, checkout_id):
    """Query checkout with detailed line information including gift lines."""
    query = """
    query Checkout($checkoutId: ID!){
      checkout(id: $checkoutId){
        id
        totalPrice{
          gross{
            amount
          }
        }
        lines {
          id
          isGift
          quantity
          variant {
            id
            name
          }
          unitPrice {
            gross {
              amount
            }
          }
          totalPrice {
            gross {
              amount
            }
          }
          undiscountedUnitPrice {
            amount
          }
        }
      }
    }
    """
    variables = {"checkoutId": checkout_id}
    response = api_client.post_graphql(query, variables)
    content = response.json()
    assert "errors" not in content, f"GraphQL errors: {content.get('errors')}"
    return content["data"]["checkout"]


@pytest.mark.e2e
def test_checkout_gift_promotion_update_flow(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_discounts,
    shop_permissions,
):
    """Test gift promotion update flow in checkout.

    Checks:
    - Gift line is added when promotion is active
    - Gift line updates when the promotion's gift variant changes
    - Discount recalculation reflects updated gift variant and prices
    - Checkout completes successfully with correct gift line in order
    """
    # Setup permissions
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    # Prepare shop data
    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    # Prepare regular product (to be purchased)
    variant_price = 50
    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
        product_type_slug="regular-product",
    )

    # Prepare another product (to be purchased)
    variant_price = 25
    (
        _product_id_2,
        product_variant_id_2,
        _product_variant_price_2,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
        product_type_slug="new-product",
    )

    # Prepare two gift products (different variants for testing updates)
    gift1_price = 20
    (
        gift1_product_id,
        gift1_variant_id,
        _gift1_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        gift1_price,
        product_type_slug="gift-product-1",
    )

    gift2_price = 30
    (
        gift2_product_id,
        gift2_variant_id,
        _gift2_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        gift2_price,
        product_type_slug="gift-product-2",
    )

    # Step 1 - Create checkout with regular product
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testuser@example.com",
    )
    checkout_id = checkout_data["id"]
    assert checkout_data["isShippingRequired"] is True

    # Verify only one line (no gift yet)
    checkout_lines = get_checkout_with_lines(e2e_not_logged_api_client, checkout_id)
    assert len(checkout_lines["lines"]) == 1
    assert checkout_lines["lines"][0]["isGift"] is False

    # Step 2 - Create gift promotion (order promotion with gift reward)
    promotion_name = "Gift Promotion Test"
    promotion = create_promotion(
        e2e_staff_api_client,
        promotion_name,
        promotion_type="ORDER",
    )
    promotion_id = promotion["id"]

    # Create promotion rule with gift reward
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
    }

    promotion_rule_input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": "Gift Rule 1",
        "rewardType": "GIFT",
        "gifts": [gift1_variant_id],
        "orderPredicate": order_predicate,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_rule_input,
    )
    promotion_rule_id = promotion_rule["id"]

    # Step 3 - Update shipping method - this should trigger discount recalculation
    # and add the gift line
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Verify gift line was added
    checkout_lines = get_checkout_with_lines(e2e_not_logged_api_client, checkout_id)
    assert len(checkout_lines["lines"]) == 2

    # Find gift line
    gift_lines = [line for line in checkout_lines["lines"] if line["isGift"]]
    regular_lines = [line for line in checkout_lines["lines"] if not line["isGift"]]

    assert len(gift_lines) == 1
    assert len(regular_lines) == 1

    # Verify gift line details
    gift_line = gift_lines[0]
    assert gift_line["variant"]["id"] == gift1_variant_id
    assert gift_line["unitPrice"]["gross"]["amount"] == 0  # Gift should be free
    assert gift_line["totalPrice"]["gross"]["amount"] == 0
    assert gift_line["undiscountedUnitPrice"]["amount"] == gift1_price

    # Step 4 - Update gift promotion - change to different gift variant
    promotion_rule_update_input = {
        "addGifts": [gift2_variant_id],
        "removeGifts": [gift1_variant_id],
    }
    update_promotion_rule(
        e2e_staff_api_client,
        promotion_rule_id,
        promotion_rule_update_input,
    )

    # Step 6 - Fetch checkout after promotion update.
    # The gift line should still be the old variant (gift1), as checkout prices
    # do not expired.
    checkout_lines = get_checkout_with_lines(e2e_not_logged_api_client, checkout_id)
    assert len(checkout_lines["lines"]) == 2

    gift_lines = [line for line in checkout_lines["lines"] if line["isGift"]]
    assert len(gift_lines) == 1

    # Gift line should still be the original variant
    gift_line = gift_lines[0]
    assert gift_line["variant"]["id"] == gift1_variant_id
    assert gift_line["unitPrice"]["gross"]["amount"] == 0
    assert gift_line["totalPrice"]["gross"]["amount"] == 0
    assert gift_line["undiscountedUnitPrice"]["amount"] == gift1_price

    # Step 6 - Add new checkout line - this should trigger discount recalculation
    # and update the gift line to new variant
    checkout_data = checkout_lines_add(
        e2e_not_logged_api_client,
        checkout_id,
        [{"variantId": product_variant_id_2, "quantity": 1}],
    )

    # Verify gift line was updated (new variant, new line ID)
    checkout_lines = get_checkout_with_lines(e2e_not_logged_api_client, checkout_id)
    assert len(checkout_lines["lines"]) == 3

    gift_lines = [line for line in checkout_lines["lines"] if line["isGift"]]
    assert len(gift_lines) == 1

    # Verify the gift line changed
    updated_gift_line = gift_lines[0]
    # Verify the gift line changed to the new variant
    assert updated_gift_line["variant"]["id"] == gift2_variant_id

    # Verify new variant details
    assert updated_gift_line["variant"]["id"] == gift2_variant_id
    assert updated_gift_line["unitPrice"]["gross"]["amount"] == 0  # Still free
    assert updated_gift_line["totalPrice"]["gross"]["amount"] == 0
    assert updated_gift_line["undiscountedUnitPrice"]["amount"] == gift2_price

    # Find and validate regular line for product_variant_id
    regular_line_1 = next(
        line
        for line in checkout_lines["lines"]
        if not line["isGift"] and line["variant"]["id"] == product_variant_id
    )
    assert regular_line_1["unitPrice"]["gross"]["amount"] == 50

    # Find and validate regular line for product_variant_id_2
    regular_line_2 = next(
        line
        for line in checkout_lines["lines"]
        if not line["isGift"] and line["variant"]["id"] == product_variant_id_2
    )
    assert regular_line_2["unitPrice"]["gross"]["amount"] == 25

    # Step 7 - Complete checkout
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Create payment (only for regular product, gift is free)
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Complete checkout
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )

    # Verify order was created successfully
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount

    # Verify order has both lines (regular + gift)
    order_lines = order_data["lines"]
    assert len(order_lines) == 3

    # Verify gift line in order
    order_gift_lines = [line for line in order_lines if line["isGift"]]
    assert len(order_gift_lines) == 1

    order_gift_line = order_gift_lines[0]
    assert order_gift_line["variant"]["id"] == gift2_variant_id
    assert order_gift_line["unitPrice"]["gross"]["amount"] == 0
    assert order_gift_line["totalPrice"]["gross"]["amount"] == 0
