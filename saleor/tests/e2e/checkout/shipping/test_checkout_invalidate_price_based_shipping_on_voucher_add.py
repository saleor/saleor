import pytest

from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...utils import assign_permissions
from ...vouchers.utils import create_voucher, create_voucher_channel_listing
from ..utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_lines_add,
    raw_checkout_add_promo_code,
)


def prepare_entire_order_voucher(e2e_staff_api_client, channel_id, voucher_amount):
    voucher_code = "ENTIRE_ORDER"
    input = {
        "name": "Entire order voucher",
        "addCodes": [voucher_code],
        "applyOncePerCustomer": False,
        "applyOncePerOrder": False,
        "onlyForStaff": False,
        "discountValueType": "FIXED",
        "endDate": None,
        "minCheckoutItemsQuantity": 0,
        "startDate": None,
        "type": "ENTIRE_ORDER",
        "usageLimit": None,
        "singleUse": False,
    }
    voucher_data = create_voucher(e2e_staff_api_client, input)
    voucher_id = voucher_data["id"]
    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": voucher_amount,
        },
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_code


@pytest.mark.e2e
def test_checkout_should_invalidate_shipping_methods_when_adding_entire_order_voucher_0116(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_settings,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_settings,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data, _ = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [
                            {"add_channels": {"minimum_order_price": 18.0}}
                        ],
                    },
                ],
                "order_settings": {},
            }
        ],
        shop_settings={},
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=18,
    )

    voucher_amount = 1
    voucher_code = prepare_entire_order_voucher(
        e2e_staff_api_client, channel_id, voucher_amount
    )

    # Step 1 - Create checkout for product
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
    checkout_lines = checkout_data["lines"][0]
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_lines["unitPrice"]["gross"]["amount"] == float(
        product_variant_price
    )
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == product_variant_price

    # Step 2 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 3 Add voucher code to checkout. Selected delivery method should be unset as
    # the price is lower than the minimum total price for this method.
    checkout_data = raw_checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )

    assert checkout_data["checkout"]["voucherCode"] == voucher_code
    assert checkout_data["checkout"]["discount"]["amount"] == voucher_amount
    assert checkout_data["checkout"]["deliveryMethod"] is None

    # Step 4 Add lines to the checkout to increase the total amount
    lines_add = [
        {
            "variantId": product_variant_id,
            "quantity": 2,
        },
    ]
    checkout_data = checkout_lines_add(
        e2e_staff_api_client,
        checkout_id,
        lines_add,
    )
    checkout_lines = checkout_data["lines"][0]
    assert checkout_lines["quantity"] == 3
    subtotal_amount = float(product_variant_price) * 3 - voucher_amount
    assert checkout_lines["totalPrice"]["gross"]["amount"] == subtotal_amount

    # Step 5 Add shipping method again.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = float(checkout_data["shippingPrice"]["gross"]["amount"])
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

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
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["discounts"][0]["value"] == voucher_amount
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price
