import pytest

from ...product.utils.preparing_product import prepare_product
from ...shop.utils import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ...warehouse.utils import update_warehouse
from ..utils import (
    checkout_billing_address_update,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    get_checkout,
)


@pytest.mark.e2e
def test_calculate_simple_taxes_order_with_click_and_collect_with_prices_entered_with_tax_true_CORE_2012(
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
    }

    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "us shipping zone",
                            }
                        ],
                    },
                    {
                        "countries": ["DE"],
                        "shipping_methods": [
                            {
                                "name": "de shipping zone",
                            }
                        ],
                    },
                ],
                "order_settings": {},
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    collection_point_id = shop_data[0]["warehouse_id"]
    update_warehouse(
        e2e_staff_api_client,
        collection_point_id,
        is_private=False,
        click_and_collect_option="LOCAL",
    )
    shipping_country_tax_rate = 21
    shipping_country_code = "US"
    billing_country_tax_rate = 19
    billing_country_code = "DE"

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

    variant_price = "17.77"
    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        collection_point_id,
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
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True

    assert len(checkout_data["shippingMethods"]) == 1

    # Step 2 - Set billing address for checkout
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

    # Step 3 - Get checkout and verify taxes
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

    # Step 4 - Set DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        collection_point_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == collection_point_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    assert checkout_data["shippingPrice"]["gross"]["amount"] == 0.0
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == float(variant_price)
    assert checkout_data["totalPrice"]["tax"]["amount"] == calculated_tax

    # Step 5 - Create payment for checkout
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 6 - Complete checkout
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["isShippingRequired"] is True
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["total"]["tax"]["amount"] == calculated_tax
    assert order_data["total"]["net"]["amount"] == round(
        total_gross_amount - calculated_tax, 2
    )


@pytest.mark.e2e
def test_calculate_simple_taxes_order_with_click_and_collect_with_prices_entered_with_tax_false_CORE_2012(
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
        "prices_entered_with_tax": False,
    }

    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "us shipping zone",
                            }
                        ],
                    },
                    {
                        "countries": ["DE"],
                        "shipping_methods": [
                            {
                                "name": "de shipping zone",
                            }
                        ],
                    },
                ],
                "order_settings": {},
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    collection_point_id = shop_data[0]["warehouse_id"]
    update_warehouse(
        e2e_staff_api_client,
        collection_point_id,
        is_private=False,
        click_and_collect_option="LOCAL",
    )
    shipping_country_tax_rate = 21
    shipping_country_code = "US"
    billing_country_tax_rate = 19
    billing_country_code = "DE"

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

    variant_price = "17.77"
    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        collection_point_id,
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
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True

    assert len(checkout_data["shippingMethods"]) == 1

    # Step 2 - Set billing address for checkout
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

    # Step 3 - Get checkout and verify taxes
    checkout_data = get_checkout(e2e_not_logged_api_client, checkout_id)
    subtotal_net = round(float(variant_price), 2)
    calculated_tax = round(subtotal_net * (shipping_country_tax_rate / 100), 2)
    subtotal_gross = subtotal_net + calculated_tax
    assert checkout_data["totalPrice"]["gross"]["amount"] == subtotal_gross
    assert checkout_data["totalPrice"]["net"]["amount"] == subtotal_net
    assert checkout_data["totalPrice"]["tax"]["amount"] == calculated_tax

    # Step 4 - Set DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        collection_point_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == collection_point_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert checkout_data["shippingPrice"]["gross"]["amount"] == 0.0
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == subtotal_gross
    assert checkout_data["totalPrice"]["tax"]["amount"] == calculated_tax

    # Step 5 - Create payment for checkout
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 6 - Complete checkout
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["isShippingRequired"] is True
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["total"]["tax"]["amount"] == calculated_tax
    assert order_data["total"]["net"]["amount"] == round(
        total_gross_amount - calculated_tax, 2
    )
