from decimal import Decimal

import pytest

from ......checkout.models import Checkout
from ......discount import DiscountType, RewardValueType
from ....product.utils.preparing_product import prepare_product
from ....promotions.utils import create_promotion, create_promotion_rule
from ....shop.utils.preparing_shop import prepare_default_shop
from ....utils import assign_permissions
from ...utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_lines_update,
)


def prepare_promotion(e2e_staff_api_client):
    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    promotion_name = "Promotion"
    promotion_type = "ORDER"

    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type
    )

    promotion_id = promotion_data["id"]
    discount_value = 25
    order_predicate_subtotal_value = "79.96"
    order_predicate_total_value = "89.96"
    order_predicate = {
        "AND": [
            {
                "discountedObjectPredicate": {
                    "baseSubtotalPrice": {"eq": order_predicate_subtotal_value}
                }
            },
            {
                "discountedObjectPredicate": {
                    "baseTotalPrice": {"eq": order_predicate_total_value},
                }
            },
        ]
    }

    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": "test rule",
        "orderPredicate": order_predicate,
        "rewardType": "SUBTOTAL_DISCOUNT",
        "rewardValue": discount_value,
        "rewardValueType": "PERCENTAGE",
    }

    promotion_rule = create_promotion_rule(e2e_staff_api_client, input)
    promotion_rule_id = promotion_rule["id"]
    assert promotion_rule["orderPredicate"] == order_predicate
    assert promotion_rule["channels"][0]["id"] == channel_id

    return (
        channel_id,
        channel_slug,
        shipping_method_id,
        warehouse_id,
        promotion_id,
        promotion_rule_id,
        discount_value,
        order_predicate_total_value,
        order_predicate_subtotal_value,
    )


@pytest.mark.e2e
def test_promotion_discount_applied_on_checkout_with_specific_total_and_subtotal_CORE_2134(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
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

    (
        channel_id,
        channel_slug,
        shipping_method_id,
        warehouse_id,
        promotion_id,
        promotion_rule_id,
        discount_value,
        order_predicate_total_value,
        order_predicate_subtotal_value,
    ) = prepare_promotion(e2e_staff_api_client)
    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=19.99
    )

    # Step 1 - Create checkout with 1 product variant
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = data["id"]
    checkout_db = Checkout.objects.first()
    total = data["totalPrice"]["gross"]["amount"]
    subtotal = data["subtotalPrice"]["gross"]["amount"]
    assert data["billingAddress"] is not None
    assert data["shippingAddress"] is not None
    assert checkout_id is not None
    assert data["lines"][0]["variant"]["id"] == product_variant_id
    assert data["discount"]["amount"] == 0.00
    assert total != order_predicate_total_value
    assert subtotal != order_predicate_subtotal_value
    assert not checkout_db.discounts.all()

    # Step 2 - Add shipping method
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    shipping_price = checkout_data["shippingPrice"]["gross"]["amount"]
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 3 - Update checkout lines to 4 product variants
    lines = [{"variantId": product_variant_id, "quantity": 4}]
    checkout_lines = checkout_lines_update(
        e2e_not_logged_api_client, checkout_id, lines
    )
    discounted_subtotal = checkout_lines["checkout"]["subtotalPrice"]["gross"]["amount"]
    total_gross = checkout_lines["checkout"]["totalPrice"]["gross"]["amount"]
    undiscounted_subtotal = checkout_lines["checkout"]["lines"][0][
        "undiscountedTotalPrice"
    ]["amount"]
    undiscounted_total = undiscounted_subtotal + shipping_price
    discount = round(float(undiscounted_subtotal) * discount_value / 100, 2)
    discounted_total = discounted_subtotal + shipping_price
    assert discounted_subtotal == undiscounted_subtotal - discount
    assert checkout_lines["checkout"]["discount"]["amount"] == discount
    assert total_gross != total
    assert total_gross == discounted_total
    assert undiscounted_total == float(order_predicate_total_value)
    assert undiscounted_subtotal == float(order_predicate_subtotal_value)
    discounts_db = checkout_db.discounts.all()
    assert len(discounts_db) == 1
    discount_db = discounts_db[0]
    assert discount_db.type == DiscountType.ORDER_PROMOTION.lower()
    assert discount_db.value == Decimal(discount_value)
    assert discount_db.value_type == RewardValueType.PERCENTAGE.lower()
    assert discount_db.amount_value == Decimal(str(discount))

    # Step 4 - Create payment
    checkout_dummy_payment_create(e2e_not_logged_api_client, checkout_id, total_gross)

    # Step 5 - Complete the checkout
    order_data = checkout_complete(e2e_not_logged_api_client, checkout_id)
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == discounted_total
