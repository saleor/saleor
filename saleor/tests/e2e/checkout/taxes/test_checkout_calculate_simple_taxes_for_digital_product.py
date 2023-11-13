import pytest

from ...product.utils.preparing_product import prepare_digital_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    checkout_billing_address_update,
    checkout_complete,
    checkout_create,
    checkout_dummy_payment_create,
    get_checkout,
)


@pytest.mark.e2e
def test_digital_checkout_calculate_simple_tax_based_on_billing_country_CORE_2007(
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
        currency="CZK",
        country="CZ",
        countries=["CZ", "US"],
        shipping_country_code="US",
        shipping_country_tax_rate=9,
        billing_country_code="CZ",
        billing_country_tax_rate=21,
        prices_entered_with_tax=False,
        shipping_price=15.0,
        shipping_zones_structure=[
            {"countries": ["CZ", "US"], "num_shipping_methods": 1}
        ],
    )
    warehouse_id = shop_data["warehouse_id"]
    channel_id = shop_data["channel_id"]
    channel_slug = shop_data["channel_slug"]
    billing_country_tax_rate = shop_data["billing_country_tax_rate"]
    billing_country_code = shop_data["billing_country_code"]
    update_country_tax_rates(
        e2e_staff_api_client,
        billing_country_code,
        [{"rate": billing_country_tax_rate}],
    )
    variant_price = 88.89
    _product_id, product_variant_id, product_variant_price = prepare_digital_product(
        e2e_staff_api_client, channel_id, warehouse_id, variant_price
    )
    product_variant_price = float(product_variant_price)

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
    assert checkout_data["isShippingRequired"] is False

    # Step 2 - Set billing address for checkout.
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
    checkout_billing_address_update(e2e_staff_api_client, checkout_id, billing_address)

    # Step 3 - Get checkout and verify taxes
    checkout_data = get_checkout(e2e_not_logged_api_client, checkout_id)
    calculated_tax = round(
        (product_variant_price * (billing_country_tax_rate / 100)),
        2,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    assert checkout_data["totalPrice"]["net"]["amount"] == product_variant_price
    assert checkout_data["totalPrice"]["tax"]["amount"] == calculated_tax
    assert total_gross_amount == product_variant_price + calculated_tax

    # Step 4 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 5 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["paymentStatus"] == "FULLY_CHARGED"
    assert order_data["total"]["net"]["amount"] == product_variant_price
    assert order_data["total"]["tax"]["amount"] == calculated_tax
    assert (
        order_data["total"]["gross"]["amount"] == product_variant_price + calculated_tax
    )
