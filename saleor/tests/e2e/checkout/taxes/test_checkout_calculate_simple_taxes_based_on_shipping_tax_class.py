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
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_taxes,
    permission_manage_settings,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_taxes,
        permission_manage_settings,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_shop(
        e2e_staff_api_client,
        shipping_country_tax_rate=8,
        billing_country_tax_rate=10,
        prices_entered_with_tax=False,
    )
    warehouse_id = shop_data["warehouse_id"]
    channel_id = shop_data["channel_id"]
    channel_slug = shop_data["channel_slug"]
    shipping_method_id = shop_data["shipping_method_id"]
    shipping_country_tax_rate = shop_data["shipping_country_tax_rate"]
    shipping_country_code = shop_data["shipping_country_code"]
    shipping_tax_class_id = shop_data["shipping_tax_class_id"]
    update_country_tax_rates(
        e2e_staff_api_client,
        shipping_country_code,
        [{"rate": shipping_country_tax_rate}],
    )

    update_shipping_price(
        e2e_staff_api_client,
        shipping_method_id,
        {"taxClass": shipping_tax_class_id},
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
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]

    subtotal_net = round((product_variant_price * 2), 2)
    subtotal_tax = round(subtotal_net * (shipping_country_tax_rate / 100), 2)
    subtotal_gross = subtotal_net + subtotal_tax

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["totalPrice"]["gross"]["amount"] == subtotal_gross
    assert checkout_data["totalPrice"]["tax"]["amount"] == subtotal_tax
    assert checkout_data["totalPrice"]["net"]["amount"] == subtotal_net

    # Step 2 - Set DeliveryMethod for checkout and check prices
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    shipping_net_price = checkout_data["deliveryMethod"]["price"]["amount"]

    shipping_net = shipping_net_price
    shipping_tax = round(shipping_net * (shipping_country_tax_rate / 100), 2)
    shipping_gross = shipping_net + shipping_tax

    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["shippingPrice"]["net"]["amount"] == shipping_net
    assert checkout_data["shippingPrice"]["tax"]["amount"] == shipping_tax
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
