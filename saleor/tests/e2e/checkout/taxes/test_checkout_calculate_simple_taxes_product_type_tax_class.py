import pytest

from ...product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
    update_product_type,
)
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ..utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


def prepare_product(
    e2e_staff_api_client,
    warehouse_id,
    channel_id,
    variant_price,
):
    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id = product_data["id"]

    create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        channel_id,
    )

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    product_variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=stocks,
    )
    product_variant_id = product_variant_data["id"]

    product_variant_channel_listing_data = create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        variant_price,
    )
    product_variant_price = product_variant_channel_listing_data["channelListings"][0][
        "price"
    ]["amount"]

    return product_variant_id, product_variant_price, product_type_id


@pytest.mark.e2e
def test_checkout_calculate_simple_tax_based_on_product_type_tax_class_CORE_2003(
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
        "tax_rates": [
            {
                "type": "product_type",
                "name": "Product Type Tax Rate",
                "country_code": "US",
                "rate": 8,
            },
        ],
    }
    shop_data, tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [
                            {
                                "add_channels": {},
                            }
                        ],
                    },
                ],
                "order_settings": {},
            },
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    shipping_price = 10.0
    warehouse_id = shop_data[0]["warehouse_id"]
    product_type_tax_class_id = tax_config[0]["product_type_tax_class_id"]
    product_type_tax_rate = tax_config[1]["product_type"]["rate"]
    country = "US"
    country_tax_rate = 10

    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": country_tax_rate}],
    )

    variant_price = "155.88"
    (product_variant_id, _product_variant_price, product_type_id) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )
    product_type_tax_class = {"taxClass": product_type_tax_class_id}
    update_product_type(e2e_staff_api_client, product_type_id, product_type_tax_class)

    # Step 1 - Create checkout and check prices
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
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    variant_price = float(variant_price)
    assert checkout_data["totalPrice"]["net"]["amount"] == variant_price
    calculated_tax = round(variant_price * (product_type_tax_rate / 100), 2)
    assert checkout_data["totalPrice"]["tax"]["amount"] == calculated_tax
    assert checkout_data["totalPrice"]["gross"]["amount"] == round(
        variant_price + calculated_tax, 2
    )
    # Step 2 - Set DeliveryMethod for checkout and check prices
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )

    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["shippingPrice"]["net"]["amount"] == float(shipping_price)
    shipping_tax = round((float(shipping_price) * (country_tax_rate / 100)), 2)
    assert checkout_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert (
        checkout_data["shippingPrice"]["gross"]["amount"]
        == float(shipping_price) + shipping_tax
    )

    total_tax = calculated_tax + shipping_tax
    assert checkout_data["totalPrice"]["tax"]["amount"] == total_tax
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    calculated_total = round(variant_price + shipping_price + total_tax, 2)
    assert total_gross_amount == calculated_total

    # Step 3 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 4 - Complete checkout.
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
