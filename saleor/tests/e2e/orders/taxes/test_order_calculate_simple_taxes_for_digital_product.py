import pytest

from ...product.utils.preparing_product import prepare_digital_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import draft_order_complete, draft_order_create, order_lines_create


@pytest.mark.e2e
def test_digital_order_calculate_simple_tax_based_on_billing_country_CORE_2008(
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
        "prices_entered_with_tax": True,
        "tax_rates": [
            {
                "type": "shipping_country",
                "name": "Shipping Country Tax Rate",
                "country_code": "US",
                "rate": 5,
            },
            {
                "type": "billing_country",
                "name": "Billing Country Tax Rate",
                "country_code": "DE",
                "rate": 19,
            },
        ],
    }

    shop_data = prepare_shop(
        e2e_staff_api_client,
        shipping_zones=[{"countries": ["US", "DE"]}],
        tax_settings=tax_settings,
    )
    channel_id = shop_data["channels"][0]["id"]
    warehouse_id = shop_data["warehouses"][0]["id"]
    billing_class_tax_rate = shop_data["tax_rates"].get("billing_country").get("rate")
    billing_country_code = (
        shop_data["tax_rates"].get("billing_country").get("country_code")
    )
    update_country_tax_rates(
        e2e_staff_api_client,
        billing_country_code,
        [{"rate": billing_class_tax_rate}],
    )

    variant_price = 100
    _product_id, product_variant_id, product_variant_price = prepare_digital_product(
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
        (product_variant_price * billing_class_tax_rate)
        / (100 + billing_class_tax_rate),
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
