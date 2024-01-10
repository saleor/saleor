import pytest

from ....product.utils import (
    create_product_variant,
    create_product_variant_channel_listing,
)
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


def prepare_voucher_for_cheapest_product(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
    apply_once_per_order,
):
    input = {
        "addCodes": [voucher_code],
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
        "applyOncePerOrder": apply_once_per_order,
    }
    voucher_data = create_voucher(e2e_staff_api_client, input=input)
    voucher_id = voucher_data["id"]
    channel_listing = [
        {"channelId": channel_id, "discountValue": voucher_discount_value},
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_code, voucher_discount_value


@pytest.mark.e2e
@pytest.mark.parametrize(
    (
        "first_variant_price",
        "second_variant_price",
        "voucher_discount_type",
        "voucher_discount_value",
        "expected_voucher_discount",
    ),
    [
        ("19.99", "109.99", "PERCENTAGE", 15, 3),
        ("13.33", "16.66", "FIXED", 4.44, 4.44),
    ],
)
def test_checkout_use_voucher_for_cheapest_product_0907(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    first_variant_price,
    second_variant_price,
    voucher_discount_type,
    voucher_discount_value,
    expected_voucher_discount,
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
        first_variant_id,
        first_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=first_variant_price,
    )
    variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=[{"warehouse": warehouse_id, "quantity": 10}],
    )
    second_variant_id = variant_data["id"]
    second_variant_price = second_variant_price

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        second_variant_id,
        channel_id,
        second_variant_price,
    )

    voucher_code, voucher_discount_value = prepare_voucher_for_cheapest_product(
        e2e_staff_api_client,
        channel_id,
        "test_voucher",
        voucher_discount_type,
        voucher_discount_value,
        "ENTIRE_ORDER",
        True,
    )

    # Step 1 - Create checkout for product
    lines = [
        {
            "variantId": first_variant_id,
            "quantity": 1,
        },
        {
            "variantId": second_variant_id,
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
    checkout_lines = checkout_data["lines"]

    assert checkout_data["isShippingRequired"] is True
    first_line = checkout_lines[0]
    assert first_line["variant"]["id"] == first_variant_id
    assert first_line["unitPrice"]["gross"]["amount"] == float(first_variant_price)
    second_line = checkout_lines[1]
    assert second_line["variant"]["id"] == second_variant_id
    assert second_line["unitPrice"]["gross"]["amount"] == float(second_variant_price)
    counted_subtotal_amount = round(
        float(first_variant_price) + float(second_variant_price), 2
    )

    # Step 2 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    subtotal_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert subtotal_amount == counted_subtotal_amount
    assert total_gross_amount == round(float(subtotal_amount + shipping_price), 2)

    # Step 3 Add voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    checkout_lines = checkout_data["lines"]
    first_line = checkout_lines[0]
    line_discount = expected_voucher_discount
    discounted_first_line_price = float(first_variant_price) - line_discount
    assert first_line["unitPrice"]["gross"]["amount"] == discounted_first_line_price
    assert first_line["undiscountedUnitPrice"]["amount"] == float(first_variant_price)

    second_line = checkout_lines[1]
    assert second_line["unitPrice"]["gross"]["amount"] == float(second_variant_price)
    assert second_line["undiscountedUnitPrice"]["amount"] == float(second_variant_price)
    subtotal_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert subtotal_amount == round(
        discounted_first_line_price + float(second_variant_price), 2
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == round(subtotal_amount + shipping_price, 2)

    # Step 4 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 5 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["discounts"][0]["value"] == line_discount
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
    first_order_line = order_data["lines"][0]
    assert (
        first_order_line["unitPrice"]["gross"]["amount"] == discounted_first_line_price
    )
    second_order_line = order_data["lines"][1]
    assert second_order_line["unitPrice"]["gross"]["amount"] == float(
        second_variant_price
    )
