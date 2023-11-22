import pytest

from ...product.utils.preparing_product import prepare_product
from ...shop.utils import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    checkout_billing_address_update,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_shipping_address_update,
    get_checkout,
)


@pytest.mark.e2e
def test_checkout_calculate_simple_tax_based_on_shipping_country_CORE_2001(
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
                "type": "shipping_country",
                "name": "Shipping Country Tax Class",
                "country_code": "CZ",
                "rate": 21,
            },
            {
                "type": "billing_country",
                "name": "Billing Country Tax Class",
                "country_code": "DE",
                "rate": 19,
            },
        ],
    }
    shipping_method_channel_listing_settings = {
        "price": "6.66",
    }
    shop_data = prepare_shop(
        e2e_staff_api_client,
        shipping_zones=[{"countries": ["CZ", "US", "DE"]}],
        tax_settings=tax_settings,
        shipping_method_channel_listing_settings=shipping_method_channel_listing_settings,
    )
    channel_id = shop_data["channels"][0]["id"]
    channel_slug = shop_data["channels"][0]["slug"]
    shipping_method_id = shop_data["shipping_methods"][0]["id"]
    shipping_price = shop_data["shipping_methods"][0]["price"]
    warehouse_id = shop_data["warehouses"][0]["id"]
    shipping_class_tax_rate = shop_data["tax_rates"].get("shipping_country").get("rate")
    shipping_country_code = (
        shop_data["tax_rates"].get("shipping_country").get("country_code")
    )
    billing_class_tax_rate = shop_data["tax_rates"].get("billing_country").get("rate")
    billing_country_code = (
        shop_data["tax_rates"].get("billing_country").get("country_code")
    )

    update_country_tax_rates(
        e2e_staff_api_client,
        shipping_country_code,
        [{"rate": shipping_class_tax_rate}],
    )
    update_country_tax_rates(
        e2e_staff_api_client,
        billing_country_code,
        [{"rate": billing_class_tax_rate}],
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

    # Step 1 - Create checkout
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

    # Step 2 - Set shipping address for checkout
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

    # Step 3 - Set billing address for checkout
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
        (float(variant_price) * shipping_class_tax_rate)
        / (100 + shipping_class_tax_rate),
        2,
    )
    assert checkout_data["totalPrice"]["tax"]["amount"] == calculated_tax
    assert (
        checkout_data["totalPrice"]["net"]["amount"]
        == float(variant_price) - calculated_tax
    )

    # Step 5 - Set DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    assert checkout_data["shippingPrice"]["gross"]["amount"] == float(shipping_price)
    shipping_tax = round(
        (float(shipping_price) * shipping_class_tax_rate)
        / (100 + shipping_class_tax_rate),
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

    # Step 6 - Create payment for checkout
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 7 - Complete checkout
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
