import pytest

from ... import DEFAULT_ADDRESS
from ...product.utils import update_product
from ...product.utils.preparing_product import prepare_product
from ...shop.utils import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
)


@pytest.mark.e2e
def test_order_calculate_simple_tax_based_on_shipping_tax_class_CORE_2010(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_taxes,
    permission_manage_orders,
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
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_shop(
        e2e_staff_api_client,
        country_tax_rate=10,
        shipping_country_tax_rate=8,
        prices_entered_with_tax=True,
    )
    channel_id = shop_data["channel_id"]
    warehouse_id = shop_data["warehouse_id"]
    shipping_price = shop_data["shipping_price"]
    shipping_method_id = shop_data["shipping_method_id"]
    shipping_country_tax_rate = shop_data["shipping_country_tax_rate"]
    country_tax_rate = shop_data["country_tax_rate"]
    country_tax_class_id = shop_data["country_tax_class_id"]
    country = shop_data["country"]
    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": shipping_country_tax_rate}],
    )
    variant_price = "33.33"
    (product_id, product_variant_id, product_variant_price) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    tax_class = {"taxClass": country_tax_class_id}
    update_product(e2e_staff_api_client, product_id, tax_class)

    # Step 1 - Create a draft order
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        input,
    )
    product_variant_price = float(product_variant_price)
    order_id = data["order"]["id"]

    # Step 2 - Add product to draft order and check prices
    lines = [{"variantId": product_variant_id, "quantity": 2}]
    order_data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_data = order_data["order"]
    shipping_method_id = order_data["shippingMethods"][0]["id"]
    shipping_price = order_data["shippingMethods"][0]["price"]["amount"]
    shipping_price = float(shipping_price)

    subtotal_gross = round((product_variant_price * 2), 2)

    subtotal_tax = round(
        (subtotal_gross * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    subtotal_net = round(subtotal_gross - subtotal_tax, 2)

    assert order_data["isShippingRequired"] is True
    assert order_data["total"]["gross"]["amount"] == subtotal_gross
    assert order_data["total"]["tax"]["amount"] == subtotal_tax
    assert order_data["total"]["net"]["amount"] == subtotal_net

    # Step 3 - Add a shipping method to the order and check prices
    input = {"shippingMethod": shipping_method_id}
    order_data = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_data = order_data["order"]

    shipping_gross = shipping_price
    shipping_tax = round(
        (shipping_price * shipping_country_tax_rate)
        / (shipping_country_tax_rate + 100),
        2,
    )
    shipping_net = round(shipping_price - shipping_tax, 2)

    assert order_data["deliveryMethod"]["id"] == shipping_method_id
    assert order_data["shippingPrice"]["net"]["amount"] == shipping_net
    assert order_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_gross

    total_gross_amount = subtotal_gross + shipping_gross
    total_net_amount = subtotal_net + shipping_net
    total_tax_amount = subtotal_tax + shipping_tax

    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["total"]["tax"]["amount"] == total_tax_amount
    assert order_data["total"]["net"]["amount"] == total_net_amount

    # Step 4 - Complete the draft order
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] == "UNFULFILLED"
    assert order["order"]["paymentStatus"] == "NOT_CHARGED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["total"]["tax"]["amount"] == total_tax_amount
    assert order_data["total"]["net"]["amount"] == total_net_amount
    assert order_data["shippingPrice"]["net"]["amount"] == shipping_net
    assert order_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_gross
