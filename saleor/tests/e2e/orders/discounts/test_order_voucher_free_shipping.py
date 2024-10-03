import pytest

from .....product.tasks import recalculate_discounted_price_for_products_task
from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ...vouchers.utils import (
    create_voucher,
    create_voucher_channel_listing,
)
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
    order_update_shipping,
)


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
        "singleUse": True,
    }
    voucher_data = create_voucher(e2e_staff_api_client, input)

    voucher_id = voucher_data["id"]
    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": voucher_discount_value,
        },
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_code, voucher_discount_value


@pytest.mark.e2e
def test_draft_order_with_voucher_free_shipping_CORE_0932(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shipping_price = 10
    product_price = 33.33

    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "display_gross_prices": False,
        "prices_entered_with_tax": True,
    }

    # Create channel, warehouse, shipping method and update tax configuration
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
                                "add_channels": {
                                    "price": shipping_price,
                                },
                            }
                        ],
                    }
                ],
                "order_settings": {
                    "automaticallyConfirmAllNewOrders": True,
                    "allowUnpaidOrders": False,
                    "includeDraftOrderInVoucherUsage": False,
                },
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]

    country_tax_rate = 10
    country = "US"

    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": country_tax_rate}],
    )
    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=product_price
    )

    # Prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Create voucher entire order
    voucher_code, voucher_discount_value = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="free-shipping",
        voucher_discount_type="PERCENTAGE",
        voucher_discount_value=100,
        voucher_type="SHIPPING",
    )

    # Step 1 - Create a draft order
    input = {
        "channelId": channel_id,
        "userEmail": "customer@example.com",
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 2 - Add order lines to the order
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_line = order["order"]["lines"][0]

    # Assert lines:
    assert order_line["variant"]["id"] == product_variant_id
    assert order_line["unitPrice"]["gross"]["amount"] == product_variant_price

    # Assert subtotal:
    expected_subtotal_gross = product_variant_price
    assert order["order"]["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    expected_subtotal_tax = round(
        (expected_subtotal_gross * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["order"]["subtotal"]["tax"]["amount"] == expected_subtotal_tax

    # Step 3 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    order = order_update_shipping(e2e_staff_api_client, order_id, input)
    assert order["order"]["deliveryMethod"]["id"] is not None

    # Assert shipping price
    assert order["order"]["shippingPrice"]["gross"]["amount"] == shipping_price
    expected_shipping_tax = round(
        (shipping_price * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["order"]["shippingPrice"]["tax"]["amount"] == expected_shipping_tax

    # Assert subtotal is the same as before adding shipping method
    assert order["order"]["subtotal"]["gross"]["amount"] == expected_subtotal_gross

    # Assert total after adding shipping method
    expected_total_gross = round(expected_subtotal_gross + shipping_price, 2)
    assert order["order"]["total"]["gross"]["amount"] == expected_total_gross
    expected_total_tax = round(expected_subtotal_tax + expected_shipping_tax, 2)
    assert order["order"]["total"]["tax"]["amount"] == expected_total_tax

    # Step 4 - Add voucher free shipping
    order = draft_order_update(
        e2e_staff_api_client, order_id, {"voucherCode": voucher_code}
    )
    # Assert voucher
    assert order["order"]["voucherCode"] == voucher_code
    assert order["order"]["discounts"][0]["type"] == "VOUCHER"
    assert order["order"]["discounts"][0]["value"] == voucher_discount_value
    assert order["order"]["discounts"][0]["amount"]["amount"] == shipping_price

    # Assert subtotal with voucher
    assert order["order"]["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    assert order["order"]["subtotal"]["tax"]["amount"] == expected_subtotal_tax

    # Assert shipping price is 0
    assert order["order"]["shippingPrice"]["gross"]["amount"] == 0
    assert order["order"]["shippingPrice"]["tax"]["amount"] == 0
    assert order["order"]["undiscountedShippingPrice"]["amount"] == shipping_price

    # Assert total with voucher
    total_gross_with_voucher = expected_subtotal_gross
    assert order["order"]["total"]["gross"]["amount"] == total_gross_with_voucher
    total_tax_with_voucher = expected_subtotal_tax
    assert order["order"]["total"]["tax"]["amount"] == total_tax_with_voucher

    # Step 5 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    completed_order = order["order"]
    assert completed_order["status"] == "UNFULFILLED"
    assert completed_order["total"]["gross"]["amount"] == total_gross_with_voucher
    assert completed_order["total"]["tax"]["amount"] == total_tax_with_voucher
    assert completed_order["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    assert completed_order["subtotal"]["tax"]["amount"] == expected_subtotal_tax
    assert completed_order["shippingPrice"]["gross"]["amount"] == 0
    assert completed_order["shippingPrice"]["tax"]["amount"] == 0
