import pytest

from ....product.utils.preparing_product import prepare_product
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ....vouchers.utils import (
    create_voucher,
    create_voucher_channel_listing,
    get_voucher,
)
from ...utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_shipping_address_update,
)


def prepare_free_shipping_voucher(
    e2e_staff_api_client,
    channel_id,
    free_shipping_voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
):
    input = {
        "code": free_shipping_voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
    }
    voucher_data = create_voucher(e2e_staff_api_client, input)
    free_shipping_voucher_code_id = voucher_data["id"]
    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": voucher_discount_value,
        },
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        free_shipping_voucher_code_id,
        channel_listing,
    )

    return free_shipping_voucher_code, free_shipping_voucher_code_id


def prepare_fixed_voucher(
    e2e_staff_api_client,
    channel_id,
    fixed_voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
):
    input = {
        "code": fixed_voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
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

    return fixed_voucher_code


@pytest.mark.e2e
def test_checkout_use_fixed_voucher_core_0901(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_checkouts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=15.55,
    )
    (
        free_shipping_voucher_code,
        free_shipping_voucher_code_id,
    ) = prepare_free_shipping_voucher(
        e2e_staff_api_client,
        channel_id,
        free_shipping_voucher_code="FREESHIPPING",
        voucher_discount_type="PERCENTAGE",
        voucher_discount_value=100,
        voucher_type="SHIPPING",
    )
    fixed_voucher_code = prepare_fixed_voucher(
        e2e_staff_api_client,
        channel_id,
        fixed_voucher_code="FIXED_VOUCHER",
        voucher_discount_type="FIXED",
        voucher_discount_value=50,
        voucher_type="ENTIRE_ORDER",
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

    # Step 3 - Add free shipping voucher code to checkout
    data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        free_shipping_voucher_code,
    )
    total_gross = data["totalPrice"]["gross"]["amount"]
    assert data["shippingPrice"]["gross"]["amount"] != shipping_price
    assert data["shippingPrice"]["gross"]["amount"] == 0
    assert total_gross == subtotal_amount

    # Step 4 - Add fixed voucher code to checkout
    data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        fixed_voucher_code,
    )
    discounted_total_gross = data["totalPrice"]["gross"]["amount"]
    assert data["lines"][0]["unitPrice"]["gross"]["amount"] == 0
    assert discounted_total_gross == shipping_price

    # Step 5 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        discounted_total_gross,
    )

    # Step 6 - Complete checkout.
    order_data = checkout_complete(
        e2e_staff_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == fixed_voucher_code
    assert order_data["total"]["gross"]["amount"] == discounted_total_gross
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price
    order_line = order_data["lines"][0]
    assert order_line["unitPrice"]["gross"]["amount"] == 0
    total = order_data["total"]["gross"]["amount"]
    assert total != undiscounted_total_gross

    # Step 7 - Check the first voucher code is unused
    data = get_voucher(e2e_staff_api_client, free_shipping_voucher_code_id)
    assert data["voucher"]["used"] == 0
    assert data["voucher"]["codes"]["edges"][0]["node"]["isActive"] is True
