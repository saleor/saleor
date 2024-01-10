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
)


def prepare_voucher_for_staff_only(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": "ENTIRE_ORDER",
        "onlyForStaff": True,
    }
    voucher_data = create_voucher(e2e_staff_api_client, input)

    voucher_id = voucher_data["id"]
    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": voucher_discount_value,
        }
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_discount_value, voucher_code


@pytest.mark.e2e
def test_staff_can_use_voucher_for_staff_only_in_checkout_core_0904(
    e2e_staff_api_client,
    e2e_no_permission_staff_api_client,
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
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price="9.99",
    )

    voucher_discount_value, voucher_code = prepare_voucher_for_staff_only(
        e2e_staff_api_client,
        channel_id,
        "VOUCHER001",
        "FIXED",
        1,
    )

    # Step 1 - Create checkout for product on sale
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        e2e_no_permission_staff_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]
    checkout_lines = checkout_data["lines"][0]
    assert checkout_lines["unitPrice"]["gross"]["amount"] == float(
        product_variant_price
    )
    assert checkout_data["isShippingRequired"] is True

    # Step 2 Add voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_no_permission_staff_api_client,
        checkout_id,
        voucher_code,
    )
    unit_price_with_voucher = float(product_variant_price) - voucher_discount_value
    assert (
        checkout_data["lines"][0]["unitPrice"]["gross"]["amount"]
        == unit_price_with_voucher
    )

    # Step 4 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_no_permission_staff_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    total_gross_amount = round(unit_price_with_voucher + shipping_price, 2)
    assert checkout_data["totalPrice"]["gross"]["amount"] == total_gross_amount

    # Step 5 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_no_permission_staff_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 6 - Complete checkout.
    order_data = checkout_complete(
        e2e_no_permission_staff_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["discounts"][0]["value"] == voucher_discount_value
    order_total_gross_amount = order_data["total"]["gross"]["amount"]
    assert order_total_gross_amount == total_gross_amount
