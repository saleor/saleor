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
    checkout_billing_address_update,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_shipping_address_update,
    get_checkout,
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
    return shipping_country_tax_rate


@pytest.mark.e2e
def test_checkout_calculate_simple_tax_based_on_shipping_country_CORE_2001(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_taxes,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_taxes,
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
        shipping_country_code="CZ",
        shipping_country_tax_rate=21,
        billing_country_code="DE",
        billing_country_tax_rate=19,
        prices_entered_with_tax=True,
    )

    variant_price = "17.77"
    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    # Step 1 - Create checkout.
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
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True

    # Step 2 - Set shipping address for checkout.
    shipping_address = {
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
    checkout_data = checkout_shipping_address_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_address,
    )
    assert len(checkout_data["shippingMethods"]) == 1
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]

    # Step 3 - Set billing address for checkout.
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
    checkout_billing_address_update(e2e_staff_api_client, checkout_id, billing_address)

    # Step 4 - Get checkout and verify taxes
    checkout_data = get_checkout(e2e_not_logged_api_client, checkout_id)
    assert checkout_data["totalPrice"]["gross"]["amount"] == float(variant_price)
    calculated_tax = round(
        (float(variant_price) * shipping_country_tax_rate)
        / (100 + shipping_country_tax_rate),
        2,
    )
    assert checkout_data["totalPrice"]["tax"]["amount"] == calculated_tax
    assert (
        checkout_data["totalPrice"]["net"]["amount"]
        == float(variant_price) - calculated_tax
    )

    # Step 5 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["shippingPrice"]["gross"]["amount"] == float(shipping_price)
    shipping_tax = round(
        (float(shipping_price) * shipping_country_tax_rate)
        / (100 + shipping_country_tax_rate),
        2,
    )
    assert checkout_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert (
        checkout_data["shippingPrice"]["net"]["amount"]
        == float(shipping_price) - shipping_tax
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    calculated_total = float(variant_price) + float(shipping_price)
    assert total_gross_amount == calculated_total
    total_tax = calculated_tax + shipping_tax
    assert checkout_data["totalPrice"]["tax"]["amount"] == total_tax

    # Step 6 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 7 - Complete checkout.
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
