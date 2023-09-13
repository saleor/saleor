import pytest

from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions
from ..vouchers.utils import create_voucher, create_voucher_channel_listing
from .utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_shipping_address_update,
)


def prepare_fixed_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
):
    voucher_data = create_voucher(
        e2e_staff_api_client,
        voucher_discount_type,
        voucher_code,
        voucher_type,
    )
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

    return voucher_code


@pytest.mark.e2e
def test_checkout_use_fixed_voucher_core_0901(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        warehouse_id,
        channel_id,
        channel_slug,
        shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=30,
    )

    voucher_code = prepare_fixed_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="FIXED_VOUCHER",
        voucher_discount_type="FIXED",
        voucher_discount_value=10,
        voucher_type="ENTIRE_ORDER",
    )

    # Step 1 - Create checkout
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 2,
        },
    ]
    checkout = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout["id"]
    checkout_lines = checkout["lines"][0]
    subtotal_amount = float(product_variant_price)
    assert checkout["isShippingRequired"] is True
    total_without_shipping = checkout["totalPrice"]["gross"]["amount"]
    assert total_without_shipping == subtotal_amount * 2
    assert checkout_lines["unitPrice"]["gross"]["amount"] == subtotal_amount
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == product_variant_price

    # Step 2 - Set shipping address and delivery method
    checkout_data = checkout_shipping_address_update(
        e2e_not_logged_api_client, checkout_id
    )
    assert len(checkout_data["shippingMethods"]) == 1
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]

    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    undiscounted_total_gross = checkout_data["totalPrice"]["gross"]["amount"]
    assert undiscounted_total_gross == total_without_shipping + shipping_price

    # Step 3 - Add voucher code to checkout
    data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    discounted_total_gross = data["totalPrice"]["gross"]["amount"]
    discount_value = data["discount"]["amount"]
    assert discounted_total_gross == undiscounted_total_gross - discount_value

    # Step 4 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        discounted_total_gross,
    )

    # Step 5 - Complete checkout.
    order_data = checkout_complete(
        e2e_staff_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["total"]["gross"]["amount"] == discounted_total_gross
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price
    order_line = order_data["lines"][0]
    assert (
        order_line["unitPrice"]["gross"]["amount"]
        == float(product_variant_price) - discount_value / 2
    )
    total = order_data["total"]["gross"]["amount"]
    assert total != undiscounted_total_gross
