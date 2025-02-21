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


def prepare_percentage_voucher(
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
def test_checkout_use_percentage_voucher_core_0902(
    e2e_logged_api_client,
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
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=19.99,
    )

    voucher_code = prepare_percentage_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="PERCENTAGE_VOUCHER",
        voucher_discount_type="PERCENTAGE",
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
        e2e_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout["id"]
    checkout_lines = checkout["lines"][0]
    unit_price = float(product_variant_price)
    assert checkout["isShippingRequired"] is True
    assert checkout_lines["unitPrice"]["gross"]["amount"] == unit_price
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == float(
        product_variant_price
    )

    # Step 2 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 3 - Add voucher code to checkout
    data = checkout_add_promo_code(
        e2e_logged_api_client,
        checkout_id,
        voucher_code,
    )
    discounted_total_gross = data["totalPrice"]["gross"]["amount"]
    discounted_unit_price = data["lines"][0]["unitPrice"]["gross"]["amount"]
    voucher_discount = 2 * (round(float(product_variant_price) * 10 / 100, 2))

    assert data["discount"]["amount"] == voucher_discount
    assert discounted_total_gross == total_gross_amount - voucher_discount
    assert discounted_unit_price == unit_price - (
        round(float(product_variant_price) * 10 / 100, 2)
    )

    # Step 4 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_logged_api_client,
        checkout_id,
        discounted_total_gross,
    )

    # Step 5 - Complete checkout.
    order_data = checkout_complete(e2e_logged_api_client, checkout_id)

    order_line = order_data["lines"][0]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == discounted_total_gross
    assert order_line["undiscountedUnitPrice"]["gross"]["amount"] == float(
        product_variant_price
    )
    assert order_line["unitPrice"]["gross"]["amount"] == discounted_unit_price
