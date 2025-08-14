import pytest

from ...product.utils.preparing_product import prepare_products
from ...promotions.utils import create_promotion
from ...shop.utils.preparing_shop import prepare_shop
from ...utils import assign_permissions
from ..utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_lines_add,
    checkout_lines_update,
)


@pytest.mark.e2e
@pytest.mark.parametrize(
    "mark_as_paid_strategy",
    [
        "TRANSACTION_FLOW",
        "PAYMENT_FLOW",
    ],
)
def test_complete_0_total_checkout_with_order_promotion_and_free_shipping_method_CORE_0124(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
    permission_manage_discounts,
    mark_as_paid_strategy,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        *shop_permissions,
        permission_manage_discounts,
    ]

    assign_permissions(e2e_staff_api_client, permissions)

    fedex_price = 0
    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "FEDEX",
                                "add_channels": {
                                    "price": fedex_price,
                                },
                            }
                        ],
                    }
                ],
                "order_settings": {
                    "markAsPaidStrategy": mark_as_paid_strategy,
                },
            }
        ],
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]

    products_data = prepare_products(
        e2e_staff_api_client, warehouse_id, channel_id, [9.99, 150, 77.77]
    )
    product1_variant_id = products_data[0]["variant_id"]
    product1_variant_price = float(products_data[0]["price"])

    product2_variant_id = products_data[1]["variant_id"]
    product2_variant_price = float(products_data[1]["price"])

    product3_variant_id = products_data[2]["variant_id"]
    product3_variant_price = float(products_data[2]["price"])

    product1_quantity = 1
    product2_quantity = 1
    product3_quantity = 1

    new_product1_quantity = 3
    new_product2_quantity = 3
    new_product3_quantity = 3

    rule_input = {
        "name": "subtotal rule",
        "orderPredicate": {
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 500}}}
        },
        "rewardValue": 100,
        "rewardValueType": "PERCENTAGE",
        "rewardType": "SUBTOTAL_DISCOUNT",
        "channels": [channel_id],
    }

    create_promotion(
        e2e_staff_api_client,
        "Order promotion",
        "ORDER",
        rules=[rule_input],
    )

    # Step 1 - Create checkout for products
    lines = [
        {
            "variantId": product1_variant_id,
            "quantity": product1_quantity,
        },
        {
            "variantId": product2_variant_id,
            "quantity": product2_quantity,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]
    line1_total = round(product1_variant_price * product1_quantity, 2)
    line2_total = round(product2_variant_price * product2_quantity, 2)
    calculated_subtotal = round(line1_total + line2_total, 2)

    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal

    line1 = checkout_data["lines"][0]
    assert line1["unitPrice"]["gross"]["amount"] == product1_variant_price
    assert line1["totalPrice"]["gross"]["amount"] == line1_total
    assert line1["undiscountedTotalPrice"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["amount"] == product1_variant_price

    line2 = checkout_data["lines"][1]
    assert line2["unitPrice"]["gross"]["amount"] == product2_variant_price
    assert line2["totalPrice"]["gross"]["amount"] == line2_total
    assert line2["undiscountedTotalPrice"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["amount"] == product2_variant_price

    # Step 2 - Add more lines
    lines = [
        {
            "variantId": product3_variant_id,
            "quantity": product3_quantity,
        }
    ]
    checkout_data = checkout_lines_add(e2e_not_logged_api_client, checkout_id, lines)
    line3_total = round(product3_variant_price * product3_quantity, 2)
    calculated_subtotal = round(line1_total + line2_total + line3_total, 2)

    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["isShippingRequired"] is True

    line3 = checkout_data["lines"][2]
    assert line3["unitPrice"]["gross"]["amount"] == product3_variant_price
    assert line3["totalPrice"]["gross"]["amount"] == line3_total
    assert line3["undiscountedTotalPrice"]["amount"] == line3_total
    assert line3["undiscountedUnitPrice"]["amount"] == product3_variant_price

    # Step 3 - Update lines to apply promotion
    lines = [
        {
            "quantity": new_product1_quantity,
            "variantId": product1_variant_id,
        },
        {
            "quantity": new_product2_quantity,
            "variantId": product2_variant_id,
        },
        {
            "quantity": new_product3_quantity,
            "variantId": product3_variant_id,
        },
    ]
    checkout_data = checkout_lines_update(e2e_not_logged_api_client, checkout_id, lines)
    line1_total = round(product1_variant_price * new_product1_quantity, 2)
    line2_total = round(product2_variant_price * new_product2_quantity, 2)
    line3_total = round(product3_variant_price * new_product3_quantity, 2)
    calculated_subtotal_before_promo = round(line1_total + line2_total + line3_total, 2)

    checkout_data = checkout_data["checkout"]
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == 0
    assert checkout_data["totalPrice"]["gross"]["amount"] == 0
    assert checkout_data["discount"]["amount"] == calculated_subtotal_before_promo

    assert len(checkout_data["shippingMethods"]) == 1
    assert checkout_data["shippingMethods"][0]["id"] == shipping_method_id

    line1 = checkout_data["lines"][0]
    assert line1["unitPrice"]["gross"]["amount"] == 0
    assert line1["totalPrice"]["gross"]["amount"] == 0
    assert line1["undiscountedTotalPrice"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["amount"] == product1_variant_price

    line2 = checkout_data["lines"][1]
    assert line2["unitPrice"]["gross"]["amount"] == 0
    assert line2["totalPrice"]["gross"]["amount"] == 0
    assert line2["undiscountedTotalPrice"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["amount"] == product2_variant_price

    line3 = checkout_data["lines"][2]
    assert line3["unitPrice"]["gross"]["amount"] == 0
    assert line3["totalPrice"]["gross"]["amount"] == 0
    assert line3["undiscountedTotalPrice"]["amount"] == line3_total
    assert line3["undiscountedUnitPrice"]["amount"] == product3_variant_price

    # Step 3 - Assign delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        checkout_data["shippingMethods"][0]["id"],
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["totalPrice"]["gross"]["amount"] == 0
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == 0
    assert checkout_data["shippingPrice"]["gross"]["amount"] == 0

    # Step 4 - Complete checkout and verify created order
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNCONFIRMED"
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
    assert order_data["total"]["gross"]["amount"] == 0
    assert order_data["subtotal"]["gross"]["amount"] == 0
    assert order_data["shippingPrice"]["gross"]["amount"] == 0
    assert (
        order_data["discounts"][0]["amount"]["amount"]
        == calculated_subtotal_before_promo
    )

    assert len(order_data["lines"]) == 3
    assert len(order_data["lines"]) == 3
    line1 = order_data["lines"][0]
    assert line1["unitPrice"]["gross"]["amount"] == 0
    assert line1["totalPrice"]["gross"]["amount"] == 0
    assert line1["undiscountedTotalPrice"]["gross"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["gross"]["amount"] == product1_variant_price

    line2 = order_data["lines"][1]
    assert line2["unitPrice"]["gross"]["amount"] == 0
    assert line2["totalPrice"]["gross"]["amount"] == 0
    assert line2["undiscountedTotalPrice"]["gross"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["gross"]["amount"] == product2_variant_price

    line3 = order_data["lines"][2]
    assert line3["unitPrice"]["gross"]["amount"] == 0
    assert line3["totalPrice"]["gross"]["amount"] == 0
    assert line3["undiscountedTotalPrice"]["gross"]["amount"] == line3_total
    assert line3["undiscountedUnitPrice"]["gross"]["amount"] == product3_variant_price
