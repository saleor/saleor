import pytest

from ...product.utils import update_product
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


@pytest.mark.e2e
def test_checkout_calculate_simple_tax_based_on_product_tax_class_CORE_2005(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "display_gross_prices": False,
        "prices_entered_with_tax": True,
        "tax_rates": [
            {
                "type": "product",
                "name": "Product Tax Rate",
                "country_code": "US",
                "rate": 5,
            },
        ],
    }
    shop_data, tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [
                            {
                                "add_channels": {},
                            }
                        ],
                    },
                ],
                "order_settings": {},
            },
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    shipping_price = 10.0
    warehouse_id = shop_data[0]["warehouse_id"]
    product_tax_class_id = tax_config[0]["product_tax_class_id"]
    product_tax_rate = tax_config[1]["product"]["rate"]
    country_tax_rate = 23
    country = "US"

    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": country_tax_rate}],
    )

    variant_price = float("25.55")
    (product_id, product_variant_id, product_variant_price) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )
    product_tax_class = {"taxClass": product_tax_class_id}
    update_product(e2e_staff_api_client, product_id, input=product_tax_class)

    # Step 1 - Create checkout and check prices
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]

    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]
    assert checkout_data["isShippingRequired"] is True
    product_variant_price = float(product_variant_price)
    assert checkout_data["totalPrice"]["gross"]["amount"] == product_variant_price
    calculated_tax = round(
        (product_variant_price * product_tax_rate) / (100 + product_tax_rate),
        2,
    )
    assert checkout_data["totalPrice"]["tax"]["amount"] == calculated_tax

    assert checkout_data["totalPrice"]["net"]["amount"] == round(
        product_variant_price - calculated_tax, 2
    )

    # Step 2 - Set DeliveryMethod for checkout and check prices
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )

    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    shipping_price = float(shipping_price)
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["shippingPrice"]["gross"]["amount"] == shipping_price
    shipping_tax = round(
        (shipping_price * country_tax_rate) / (100 + country_tax_rate), 2
    )
    assert checkout_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert checkout_data["shippingPrice"]["net"]["amount"] == round(
        shipping_price - shipping_tax, 2
    )

    total_tax = calculated_tax + shipping_tax
    assert checkout_data["totalPrice"]["tax"]["amount"] == total_tax
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    calculated_total = round(product_variant_price + shipping_price, 2)
    assert total_gross_amount == calculated_total

    # Step 3 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 4 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["isShippingRequired"] is True
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["total"]["tax"]["amount"] == total_tax
    assert order_data["total"]["net"]["amount"] == round(
        calculated_total - total_tax, 2
    )
