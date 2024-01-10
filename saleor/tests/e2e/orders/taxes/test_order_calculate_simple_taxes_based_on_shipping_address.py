import pytest

from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
)


@pytest.mark.e2e
def test_order_calculate_simple_tax_based_on_shipping_address_CORE_2002(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
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
                                "add_channels": {},
                            }
                        ],
                    },
                    {
                        "countries": ["CZ"],
                        "shipping_methods": [
                            {
                                "name": "cz shipping zone",
                                "add_channels": {},
                            }
                        ],
                    },
                    {
                        "countries": ["DE"],
                        "shipping_methods": [
                            {
                                "name": "de shipping zone",
                                "add_channels": {},
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
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][2]["shipping_methods"][0]["id"]
    billing_country_tax_rate = 21
    billing_country_code = "CZ"
    shipping_country_code = "DE"
    shipping_country_tax_rate = 19

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

    # Step 4 - Add a shipping method
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

    # Step 5 - Complete the draft order
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
