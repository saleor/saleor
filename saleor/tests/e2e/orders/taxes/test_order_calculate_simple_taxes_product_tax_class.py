import pytest

from ... import DEFAULT_ADDRESS
from ...product.utils import update_product
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import (
    create_tax_class,
    get_tax_configurations,
    update_country_tax_rates,
    update_tax_configuration,
)
from ...utils import assign_permissions
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
)


def prepare_tax_configuration(
    e2e_staff_api_client,
    channel_slug,
    country_code,
    country_tax_rate,
    product_tax_rate,
    prices_entered_with_tax,
):
    tax_config_data = get_tax_configurations(e2e_staff_api_client)
    channel_tax_config = tax_config_data[0]["node"]
    assert channel_tax_config["channel"]["slug"] == channel_slug
    tax_config_id = channel_tax_config["id"]

    tax_config_data = update_tax_configuration(
        e2e_staff_api_client,
        tax_config_id,
        charge_taxes=True,
        tax_calculation_strategy="FLAT_RATES",
        display_gross_prices=True,
        prices_entered_with_tax=prices_entered_with_tax,
    )
    update_country_tax_rates(
        e2e_staff_api_client,
        country_code,
        [{"rate": country_tax_rate}],
    )

    country_rates = [{"countryCode": country_code, "rate": product_tax_rate}]
    tax_class_data = create_tax_class(
        e2e_staff_api_client,
        "Product tax class",
        country_rates,
    )
    tax_class_id = tax_class_data["id"]

    return country_tax_rate, product_tax_rate, tax_class_id


@pytest.mark.e2e
def test_order_calculate_simple_tax_based_on_product_tax_class_CORE_2006(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_taxes,
    permission_manage_orders,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_taxes,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        warehouse_id,
        channel_id,
        channel_slug,
        shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

    country_tax_rate, product_tax_rate, tax_class_id = prepare_tax_configuration(
        e2e_staff_api_client,
        channel_slug,
        country_code="US",
        country_tax_rate=20,
        product_tax_rate=13,
        prices_entered_with_tax=False,
    )

    variant_price = "1234"
    (product_id, product_variant_id, product_variant_price) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )
    product_tax_class = {"taxClass": tax_class_id}
    update_product(e2e_staff_api_client, product_id, input=product_tax_class)

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
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    product_variant_price = float(product_variant_price)

    # Step 2 - Add product to draft order and check prices
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_data = order_data["order"]
    calculated_tax = round(
        (product_variant_price * (product_tax_rate / 100)),
        2,
    )
    assert order_data["total"]["net"]["amount"] == product_variant_price
    assert order_data["total"]["tax"]["amount"] == calculated_tax
    assert order_data["total"]["gross"]["amount"] == round(
        product_variant_price + calculated_tax, 2
    )
    shipping_method_id = order_data["shippingMethods"][0]["id"]
    shipping_price = order_data["shippingMethods"][0]["price"]["amount"]

    # Step 3 - Add a shipping method to the order and check prices
    input = {"shippingMethod": shipping_method_id}
    order_data = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_data = order_data["order"]
    shipping_tax = round((shipping_price * (country_tax_rate / 100)), 2)
    total_tax = calculated_tax + shipping_tax
    calculated_net = round(product_variant_price + shipping_price, 2)

    assert order_data["shippingPrice"]["net"]["amount"] == shipping_price
    assert order_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert order_data["shippingPrice"]["gross"]["amount"] == round(
        shipping_price + shipping_tax, 2
    )

    # Step 4 - Complete the draft order
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] == "UNFULFILLED"
    assert order["order"]["paymentStatus"] == "NOT_CHARGED"
    assert order_data["total"]["tax"]["amount"] == total_tax
    assert order_data["total"]["net"]["amount"] == calculated_net
    assert order_data["total"]["gross"]["amount"] == round(
        calculated_net + total_tax, 2
    )
