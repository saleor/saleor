import pytest

from ....product.utils.preparing_product import prepare_product
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ....vouchers.utils import create_voucher, create_voucher_channel_listing
from ...utils import (
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
    products,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
        "products": products,
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

    return voucher_code


@pytest.mark.e2e
def test_checkout_voucher_should_not_cause_negative_variant_price_CORE_0911(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=10,
    )

    voucher_code = prepare_fixed_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="FIXED_VOUCHER",
        voucher_discount_type="FIXED",
        voucher_discount_value=20,
        voucher_type="SPECIFIC_PRODUCT",
        products=product_id,
    )

    # Step 1 - Create checkout
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
    )
    checkout_id = checkout["id"]
    checkout_lines = checkout["lines"][0]
    subtotal_amount = float(product_variant_price)
    assert checkout["isShippingRequired"] is True
    total_without_shipping = checkout["totalPrice"]["gross"]["amount"]
    assert total_without_shipping == subtotal_amount
    assert checkout_lines["unitPrice"]["gross"]["amount"] == subtotal_amount
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == product_variant_price

    # Step 2 - Set shipping address and delivery method
    checkout_data = checkout_shipping_address_update(
        e2e_not_logged_api_client, checkout_id
    )
    assert len(checkout_data["shippingMethods"]) == 1

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
    subtotal = data["subtotalPrice"]["gross"]["amount"]
    assert subtotal == 0
    assert discounted_total_gross == shipping_price

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
    assert order_line["unitPrice"]["gross"]["amount"] == 0
