import pytest

from ...channel.utils import create_channel
from ...product.utils.preparing_product import prepare_digital_product
from ...shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ...taxes.utils import (
    get_tax_configurations,
    update_country_tax_rates,
    update_tax_configuration,
)
from ...utils import assign_permissions
from ...warehouse.utils import create_warehouse
from ..utils import draft_order_complete, draft_order_create, order_lines_create


def prepare_shop(
    e2e_staff_api_client,
    shipping_price,
):
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    channel_slug = "channel-de"
    warehouse_ids = [warehouse_id]
    channel_data = create_channel(
        e2e_staff_api_client,
        slug=channel_slug,
        warehouse_ids=warehouse_ids,
        currency="EUR",
        country="DE",
    )
    channel_id = channel_data["id"]
    channel_ids = [channel_id]
    shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        countries=["DE", "US"],
        warehouse_ids=warehouse_ids,
        channel_ids=channel_ids,
    )
    shipping_zone_id = shipping_zone_data["id"]

    shipping_method_data = create_shipping_method(
        e2e_staff_api_client, shipping_zone_id
    )
    shipping_method_id = shipping_method_data["id"]
    create_shipping_method_channel_listing(
        e2e_staff_api_client,
        shipping_method_id,
        channel_id,
        price=shipping_price,
    )

    return (
        warehouse_id,
        channel_id,
        channel_slug,
        shipping_method_id,
        shipping_price,
    )


def prepare_tax_configuration(
    e2e_staff_api_client,
    channel_slug,
    shipping_country_code,
    shipping_country_tax_rate,
    billing_country_code,
    billing_country_tax_rate,
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
        shipping_country_code,
        [{"rate": shipping_country_tax_rate}],
    )
    update_country_tax_rates(
        e2e_staff_api_client, billing_country_code, [{"rate": billing_country_tax_rate}]
    )

    return billing_country_tax_rate


@pytest.mark.e2e
def test_digital_order_calculate_simple_tax_based_on_billing_country_CORE_2008(
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

    shipping_price = 10
    (
        warehouse_id,
        channel_id,
        channel_slug,
        shipping_method_id,
        shipping_price,
    ) = prepare_shop(e2e_staff_api_client, shipping_price)

    billing_country_tax_rate = prepare_tax_configuration(
        e2e_staff_api_client,
        channel_slug,
        shipping_country_code="US",
        shipping_country_tax_rate=5,
        billing_country_code="DE",
        billing_country_tax_rate=19,
        prices_entered_with_tax=True,
    )
    variant_price = 100
    product_id, product_variant_id, product_variant_price = prepare_digital_product(
        e2e_staff_api_client, channel_id, warehouse_id, variant_price
    )

    # Step 1 - Create a draft order
    billing_address = {
        "firstName": "John",
        "lastName": "Muller",
        "companyName": "Saleor Commerce DE",
        "streetAddress1": "Potsdamer Platz 47",
        "streetAddress2": "",
        "postalCode": "85131",
        "country": "DE",
        "city": "Pollenfeld",
        "phone": "+498421499469",
        "countryArea": "",
    }
    input = {
        "channelId": channel_id,
        "billingAddress": billing_address,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        input,
    )
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["isShippingRequired"] is False

    # Step 2 - Add product to draft order and check prices
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_data = order_data["order"]
    product_variant_price = float(product_variant_price)
    assert order_data["total"]["gross"]["amount"] == product_variant_price
    calculated_tax = round(
        (product_variant_price * billing_country_tax_rate)
        / (100 + billing_country_tax_rate),
        2,
    )
    assert order_data["total"]["tax"]["amount"] == calculated_tax
    assert order_data["total"]["net"]["amount"] == round(
        product_variant_price - calculated_tax, 2
    )

    # Step 3 - Complete the draft order
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] == "UNFULFILLED"
    assert order["order"]["paymentStatus"] == "NOT_CHARGED"
    assert order["order"]["total"]["tax"]["amount"] == calculated_tax
