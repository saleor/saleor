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
    checkout_lines_add,
    raw_checkout_add_promo_code,
)


def prepare_free_shipping_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
    min_amount_spent,
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
            "minAmountSpent": min_amount_spent,
        },
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_code


@pytest.mark.e2e
def test_checkout_use_free_shipping_voucher_with_min_spent_amount_0903(
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
        variant_price=25,
    )

    voucher_code = prepare_free_shipping_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="FREESHIPPING",
        voucher_discount_type="PERCENTAGE",
        voucher_discount_value=100,
        voucher_type="SHIPPING",
        min_amount_spent=75,
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

    # Step 2 Add voucher code to checkout
    checkout_data = raw_checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )
    assert checkout_data["errors"][0]["code"] == "VOUCHER_NOT_APPLICABLE"

    # Step 3 Add lines to the checkout to increase the total amount
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
    subtotal_amount = float(product_variant_price) * 3
    assert checkout_lines["totalPrice"]["gross"]["amount"] == subtotal_amount

    # Step 4 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == subtotal_amount + shipping_price

    # Step 5 Add free shipping voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == subtotal_amount

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
    assert order_data["discounts"][0]["value"] == shipping_price
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["total"]["gross"]["amount"] == subtotal_amount
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
    assert order_data["deliveryMethod"]["price"]["amount"] == shipping_price
    assert order_data["shippingPrice"]["gross"]["amount"] == 0
    order_line = order_data["lines"][0]
    assert order_line["unitPrice"]["gross"]["amount"] == float(product_variant_price)
