import pytest

from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    draft_order_complete,
    draft_order_create,
    order_lines_create,
    order_update_shipping,
)


def prepare_order_promotion(
    e2e_staff_api_client,
    channel_id,
    order_predicate_total_value,
    gift_ids,
):
    promotion_name = "Promotion with gifts"
    promotion_type = "ORDER"

    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type
    )
    promotion_id = promotion_data["id"]

    order_predicate = {
        "discountedObjectPredicate": {
            "baseTotalPrice": {"range": {"gte": order_predicate_total_value}}
        }
    }

    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": "gift rule",
        "orderPredicate": order_predicate,
        "rewardType": "GIFT",
        "gifts": gift_ids,
    }
    create_promotion_rule(e2e_staff_api_client, input)

    return promotion_id


@pytest.mark.e2e
def test_order_promotion_with_gift_reward_should_be_applied_to_draft_order_with_specific_subtotal_CORE_2140(
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

    shipping_price = 30
    product1_price = 60
    product2_price = 15
    country_tax_rate = 10
    country = "US"
    order_predicate_total_value = 150

    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "display_gross_prices": False,
        "prices_entered_with_tax": True,
    }

    # Create channel, warehouse, shipping method and update tax configuration
    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "us shipping zone",
                                "add_channels": {
                                    "price": shipping_price,
                                },
                            }
                        ],
                    }
                ],
                "order_settings": {
                    "automaticallyConfirmAllNewOrders": True,
                    "allowUnpaidOrders": False,
                    "includeDraftOrderInVoucherUsage": False,
                },
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]

    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": country_tax_rate}],
    )
    # Create products
    (
        _product_id,
        product1_variant_id,
        product1_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=product1_price,
        product_type_slug="shoes",
    )
    (
        _product_id,
        product2_variant_id,
        _product2_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=product2_price,
        product_type_slug="sunglasses",
    )

    # Create order promotion
    prepare_order_promotion(
        e2e_staff_api_client,
        channel_id,
        order_predicate_total_value=order_predicate_total_value,
        gift_ids=[product2_variant_id],
    )

    # Step 1 - Create a draft order for a product with fixed promotion
    input = {
        "channelId": channel_id,
        "userEmail": "customer@example.com",
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 2 - Add order lines to the order
    lines = [
        {"variantId": product1_variant_id, "quantity": 2},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    order = order["order"]

    # Assert subtotal price
    expected_subtotal_gross = round(product1_price * 2, 2)
    expected_subtotal_tax = round(
        expected_subtotal_gross * country_tax_rate / (100 + country_tax_rate), 2
    )
    assert order["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    assert order["subtotal"]["tax"]["amount"] == expected_subtotal_tax

    # Step 3 - Update shipping method
    input = {"shippingMethod": shipping_method_id}
    order = order_update_shipping(e2e_staff_api_client, order_id, input)
    order = order["order"]
    assert order["deliveryMethod"]["id"] is not None

    # Assert shipping price
    assert order["shippingPrice"]["gross"]["amount"] == shipping_price
    expected_shipping_tax = round(
        (shipping_price * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["shippingPrice"]["tax"]["amount"] == expected_shipping_tax

    # Assert total price
    expected_total_price = round(expected_subtotal_gross + shipping_price, 2)
    expected_total_tax = round(expected_subtotal_tax + expected_shipping_tax, 2)
    assert order["total"]["gross"]["amount"] == expected_total_price
    assert order["total"]["tax"]["amount"] == expected_total_tax

    # Assert gift line
    order_lines = order["lines"]
    assert len(order_lines) == 2
    gift_line = order_lines[1]
    assert gift_line["totalPrice"]["gross"]["amount"] == 0
    assert gift_line["isGift"] is True

    # Assert undiscounted total price
    assert order["undiscountedTotal"]["gross"]["amount"] == expected_total_price
    assert order["undiscountedTotal"]["tax"]["amount"] == expected_total_tax

    # Step 4 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    completed_order = order["order"]
    assert completed_order["status"] == "UNFULFILLED"
    assert completed_order["total"]["gross"]["amount"] == expected_total_price
    assert completed_order["total"]["tax"]["amount"] == expected_total_tax
    assert completed_order["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    assert completed_order["subtotal"]["tax"]["amount"] == expected_subtotal_tax
    assert completed_order["shippingPrice"]["gross"]["amount"] == shipping_price
    assert completed_order["shippingPrice"]["tax"]["amount"] == expected_shipping_tax
    assert (
        completed_order["undiscountedTotal"]["gross"]["amount"] == expected_total_price
    )
    assert completed_order["undiscountedTotal"]["tax"]["amount"] == expected_total_tax
    assert completed_order["lines"][1]["isGift"] is True
