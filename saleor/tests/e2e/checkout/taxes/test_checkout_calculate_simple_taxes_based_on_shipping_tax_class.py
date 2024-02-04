import pytest

from ...product.utils.preparing_product import prepare_product
from ...shipping_zone.utils import update_shipping_price
from ...shop.utils import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


@pytest.mark.e2e
def test_checkout_calculate_simple_tax_based_on_shipping_tax_class_CORE_2009(
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

    shipping_country = "US"
    shipping_class_tax_rate = 8
    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "display_gross_prices": False,
        "prices_entered_with_tax": False,
        "tax_rates": [
            {
                "type": "shipping_country",
                "name": "Shipping Country Tax Rate",
                "country_code": shipping_country,
                "rate": shipping_class_tax_rate,
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
    shipping_tax_class_id = tax_config[0]["shipping_country_tax_class_id"]
    shipping_class_tax_rate = tax_config[1]["shipping_country"]["rate"]
    billing_country_code = "US"
    billing_country_tax_rate = 10

    update_country_tax_rates(
        e2e_staff_api_client,
        shipping_country,
        [{"rate": shipping_class_tax_rate}],
    )
    input_data = {"taxClass": shipping_tax_class_id}
    update_shipping_price(
        e2e_staff_api_client,
        shipping_method_id,
        input_data,
    )

    variant_price = "17.87"
    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    # Step 1 - Create checkout and check prices
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 2,
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
    product_variant_price = float(product_variant_price)
    checkout_id = checkout_data["id"]

    subtotal_net = round((product_variant_price * 2), 2)
    subtotal_tax = round(subtotal_net * (shipping_class_tax_rate / 100), 2)
    subtotal_gross = subtotal_net + subtotal_tax

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["billingAddress"]["country"]["code"] == billing_country_code
    assert checkout_data["totalPrice"]["gross"]["amount"] == subtotal_gross
    assert checkout_data["totalPrice"]["tax"]["amount"] == subtotal_tax
    assert checkout_data["totalPrice"]["net"]["amount"] == subtotal_net

    # Step 2 - Set DeliveryMethod for checkout and check prices
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    shipping_net_price = shipping_price
    shipping_net = shipping_net_price
    shipping_tax = round(shipping_net * (shipping_class_tax_rate / 100), 2)
    billing_tax = round(subtotal_net * (billing_country_tax_rate / 100), 2)
    shipping_gross = shipping_net + shipping_tax

    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["shippingPrice"]["net"]["amount"] == shipping_net
    assert checkout_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert checkout_data["shippingPrice"]["tax"]["amount"] != billing_tax

    assert checkout_data["shippingPrice"]["gross"]["amount"] == shipping_gross

    total_gross_amount = round((subtotal_gross + shipping_gross), 1)
    total_net_amount = subtotal_net + shipping_net
    total_tax_amount = subtotal_tax + shipping_tax

    assert checkout_data["totalPrice"]["gross"]["amount"] == total_gross_amount
    assert checkout_data["totalPrice"]["tax"]["amount"] == total_tax_amount
    assert checkout_data["totalPrice"]["net"]["amount"] == total_net_amount

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
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["total"]["tax"]["amount"] == total_tax_amount
    assert order_data["total"]["net"]["amount"] == total_net_amount
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_gross
    assert order_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert order_data["shippingPrice"]["net"]["amount"] == shipping_net
