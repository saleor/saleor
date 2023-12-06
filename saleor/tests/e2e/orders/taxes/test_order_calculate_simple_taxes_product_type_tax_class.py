import pytest

from ... import DEFAULT_ADDRESS
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
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
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
def test_order_calculate_simple_tax_based_on_product_type_tax_class_CORE_2004(
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
                "type": "product_type",
                "name": "Product Type Tax Rate",
                "country_code": "US",
                "rate": 11,
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
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    shipping_price = 10.0
    warehouse_id = shop_data[0]["warehouse_id"]
    product_type_tax_class_id = tax_config[0]["product_type_tax_class_id"]
    product_type_tax_rate = tax_config[1]["product_type"]["rate"]
    shipping_country_tax_rate = 21
    country = "US"

    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": shipping_country_tax_rate}],
    )
    variant_price = "4.22"
    (product_variant_id, product_variant_price, product_type_id) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )
    product_type_tax_class = {"taxClass": product_type_tax_class_id}
    update_product_type(e2e_staff_api_client, product_type_id, product_type_tax_class)

    # Step 1 - Create a draft order
    input_data = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        input_data,
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
    assert order_data["total"]["gross"]["amount"] == product_variant_price
    calculated_tax = round(
        (product_variant_price * product_type_tax_rate) / (100 + product_type_tax_rate),
        2,
    )
    assert order_data["total"]["tax"]["amount"] == calculated_tax
    assert order_data["total"]["net"]["amount"] == round(
        product_variant_price - calculated_tax, 2
    )

    # Step 3 - Add a shipping method to the order and check prices
    input = {"shippingMethod": shipping_method_id}
    order_data = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_data = order_data["order"]
    shipping_price = order_data["shippingPrice"]["gross"]["amount"]
    shipping_tax = round(
        (
            shipping_price
            * shipping_country_tax_rate
            / (100 + shipping_country_tax_rate)
        ),
        2,
    )
    assert order_data["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert order_data["shippingPrice"]["net"]["amount"] == shipping_price - shipping_tax
    total_tax = calculated_tax + shipping_tax
    assert order_data["total"]["tax"]["amount"] == total_tax
    calculated_total = round(product_variant_price + shipping_price, 2)
    assert order_data["total"]["gross"]["amount"] == calculated_total

    # Step 4 - Complete the draft order
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] == "UNFULFILLED"
    assert order["order"]["paymentStatus"] == "NOT_CHARGED"
    assert order["order"]["total"]["gross"]["amount"] == calculated_total
    assert order["order"]["total"]["tax"]["amount"] == total_tax
    assert order["order"]["shippingPrice"]["tax"]["amount"] == shipping_tax
