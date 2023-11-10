import pytest

from ...channel.utils import create_channel
from ...product.utils.preparing_product import prepare_product
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
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
)


def prepare_shop_with_few_shipping_zone_countries(
    e2e_staff_api_client,
    shipping_price,
):
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    channel_slug = "test"
    warehouse_ids = [warehouse_id]
    channel_data = create_channel(
        e2e_staff_api_client,
        slug=channel_slug,
        warehouse_ids=warehouse_ids,
    )
    channel_id = channel_data["id"]
    channel_ids = [channel_id]
    shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        countries=["CZ", "DE", "US"],
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
        prices_entered_with_tax=False,
    )
    update_country_tax_rates(
        e2e_staff_api_client,
        shipping_country_code,
        [{"rate": shipping_country_tax_rate}],
    )
    update_country_tax_rates(
        e2e_staff_api_client,
        billing_country_code,
        [{"rate": billing_country_tax_rate}],
    )
    return shipping_country_tax_rate


@pytest.mark.e2e
def test_order_calculate_simple_tax_based_on_shipping_address_tax_class_CORE_2002(
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
        shipping_price,
    ) = prepare_shop_with_few_shipping_zone_countries(e2e_staff_api_client, "6.66")

    shipping_country_tax_rate = prepare_tax_configuration(
        e2e_staff_api_client,
        channel_slug,
        shipping_country_code="DE",
        shipping_country_tax_rate=19,
        billing_country_code="CZ",
        billing_country_tax_rate=21,
    )

    variant_price = "155.88"
    (_product_id, product_variant_id, product_variant_price) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    # Step 1 - Create a draft order
    input = {
        "channelId": channel_id,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        input,
    )
    order_id = data["order"]["id"]
    product_variant_price = float(product_variant_price)

    # Step 2 - Add lines to the order
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_data = order_data["order"]
    assert order_data["total"]["gross"]["amount"] == product_variant_price

    # Step 3 - Add shipping and billing addresses
    shipping_address = {
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
    billing_address = {
        "firstName": "John",
        "lastName": "Muller",
        "companyName": "Saleor Commerce CZ",
        "streetAddress1": "Sluneční 1396",
        "streetAddress2": "",
        "postalCode": "74784",
        "country": "CZ",
        "city": "Melc",
        "phone": "+420722274643",
        "countryArea": "",
    }
    input = {
        "userEmail": "test_user@test.com",
        "shippingAddress": shipping_address,
        "billingAddress": billing_address,
    }
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    assert draft_order["order"]["userEmail"] == "test_user@test.com"
    assert draft_order["order"]["shippingAddress"] is not None
    assert draft_order["order"]["billingAddress"] is not None

    # Step 3 - Add a shipping method
    input = {"shippingMethod": shipping_method_id}
    order_data = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_data = order_data["order"]
    shipping_price = order_data["shippingPrice"]["net"]["amount"]
    shipping_tax = round(shipping_price * (shipping_country_tax_rate / 100), 2)
    calculated_tax = round(product_variant_price * (shipping_country_tax_rate / 100), 2)
    assert (
        order_data["shippingPrice"]["gross"]["amount"] == shipping_price + shipping_tax
    )
    assert order_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert order_data["shippingPrice"]["net"]["amount"] == shipping_price
    total_tax = calculated_tax + shipping_tax
    calculated_total = float(variant_price) + float(shipping_price)

    assert order_data["total"]["tax"]["amount"] == total_tax
    assert order_data["total"]["net"]["amount"] == calculated_total
    assert order_data["total"]["gross"]["amount"] == total_tax + calculated_total

    # Step 4 - Complete the draft order
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] == "UNFULFILLED"
    assert order["order"]["paymentStatus"] == "NOT_CHARGED"
    assert order["order"]["total"]["net"]["amount"] == calculated_total
    assert order["order"]["total"]["tax"]["amount"] == total_tax
    assert order["order"]["total"]["gross"]["amount"] == total_tax + calculated_total
    assert order["order"]["shippingPrice"]["tax"]["amount"] == shipping_tax
