import pytest

from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    draft_order_complete,
    draft_order_create,
    order_discount_add,
    order_lines_create,
    order_update_shipping,
)


@pytest.mark.e2e
def test_manual_total_discount_fixed_should_be_applied_to_draft_order_CORE_0223(
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
    discount_value = 10
    discount_type = "FIXED"

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
        {"variantId": product2_variant_id, "quantity": 1},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    order = order["order"]

    # Assert subtotal price
    expected_subtotal_gross = round((product1_price * 2) + product2_price, 2)
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
    expected_total_gross = round(expected_subtotal_gross + shipping_price, 2)
    expected_total_tax = round(expected_subtotal_tax + expected_shipping_tax, 2)
    assert order["total"]["gross"]["amount"] == expected_total_gross
    assert order["total"]["tax"]["amount"] == expected_total_tax

    # Step 4 - Update manual total discount
    manual_discount_input = {
        "valueType": discount_type,
        "value": discount_value,
    }
    discount_data = order_discount_add(
        e2e_staff_api_client,
        order_id,
        manual_discount_input,
    )

    # Assert discounts
    discount = discount_data["order"]["discounts"][0]
    assert discount is not None
    assert discount["type"] == "MANUAL"
    assert discount["valueType"] == discount_type
    discount_amount = discount_value
    assert discount["amount"]["amount"] == discount_amount

    # Assert total price
    expected_total_gross_after_discount = round(
        expected_total_gross - discount_amount, 2
    )
    expected_total_tax_after_discount = round(
        (expected_total_gross_after_discount * country_tax_rate)
        / (100 + country_tax_rate),
        2,
    )
    order = discount_data["order"]
    assert order["total"]["gross"]["amount"] == expected_total_gross_after_discount
    assert order["total"]["tax"]["amount"] == expected_total_tax_after_discount

    # Assert undiscounted
    assert order["undiscountedTotal"]["gross"]["amount"] == expected_total_gross
    assert order["undiscountedTotal"]["tax"]["amount"] == expected_total_tax
    assert order["undiscountedShippingPrice"]["amount"] == shipping_price

    # Step 5 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    completed_order = order["order"]
    assert completed_order["status"] == "UNFULFILLED"
    assert completed_order["discounts"][0]["type"] == "MANUAL"
    assert (
        completed_order["total"]["gross"]["amount"]
        == expected_total_gross_after_discount
    )
    assert (
        completed_order["total"]["tax"]["amount"] == expected_total_tax_after_discount
    )
    assert (
        completed_order["undiscountedTotal"]["gross"]["amount"] == expected_total_gross
    )
    assert completed_order["undiscountedTotal"]["tax"]["amount"] == expected_total_tax


@pytest.mark.e2e
def test_manual_total_discount_percentage_should_be_applied_to_draft_order_CORE_0224(
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
    discount_value = 10
    discount_type = "PERCENTAGE"

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
        {"variantId": product2_variant_id, "quantity": 1},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    order = order["order"]

    # Assert subtotal price
    expected_subtotal_gross = round((product1_price * 2) + product2_price, 2)
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
    expected_total_gross = round(expected_subtotal_gross + shipping_price, 2)
    expected_total_tax = round(expected_subtotal_tax + expected_shipping_tax, 2)
    assert order["total"]["gross"]["amount"] == expected_total_gross
    assert order["total"]["tax"]["amount"] == expected_total_tax

    # Step 4 - Update manual total discount
    manual_discount_input = {
        "valueType": discount_type,
        "value": discount_value,
    }
    discount_data = order_discount_add(
        e2e_staff_api_client,
        order_id,
        manual_discount_input,
    )

    # Assert discounts
    discount = discount_data["order"]["discounts"][0]
    assert discount is not None
    assert discount["type"] == "MANUAL"
    assert discount["valueType"] == discount_type
    discount_amount = round((expected_total_gross * discount_value) / 100, 2)
    assert discount["amount"]["amount"] == discount_amount

    # Assert total price
    expected_total_gross_after_discount = round(
        expected_total_gross - discount_amount, 2
    )
    expected_total_tax_after_discount = round(
        (expected_total_gross_after_discount * country_tax_rate)
        / (100 + country_tax_rate),
        2,
    )
    order = discount_data["order"]
    assert order["total"]["gross"]["amount"] == expected_total_gross_after_discount
    assert order["total"]["tax"]["amount"] == expected_total_tax_after_discount

    # Assert undiscounted
    assert order["undiscountedTotal"]["gross"]["amount"] == expected_total_gross
    assert order["undiscountedTotal"]["tax"]["amount"] == expected_total_tax
    assert order["undiscountedShippingPrice"]["amount"] == shipping_price

    # Step 5 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    completed_order = order["order"]
    assert completed_order["status"] == "UNFULFILLED"
    assert completed_order["discounts"][0]["type"] == "MANUAL"
    assert (
        completed_order["total"]["gross"]["amount"]
        == expected_total_gross_after_discount
    )
    assert (
        completed_order["total"]["tax"]["amount"] == expected_total_tax_after_discount
    )
    assert (
        completed_order["undiscountedTotal"]["gross"]["amount"] == expected_total_gross
    )
    assert completed_order["undiscountedTotal"]["tax"]["amount"] == expected_total_tax
