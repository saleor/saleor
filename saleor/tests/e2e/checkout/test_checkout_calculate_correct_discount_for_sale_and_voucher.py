import pytest

from ..product.utils.preparing_product import prepare_product
from ..sales.utils import create_sale, create_sale_channel_listing, sale_catalogues_add
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
)


def prepare_sale_for_variant(
    e2e_staff_api_client,
    channel_id,
    product_variant_id,
    sale_discount_type,
    sale_discount_value,
):
    sale_name = "Sale"
    sale = create_sale(
        e2e_staff_api_client,
        sale_name,
        sale_discount_type,
    )
    sale_id = sale["id"]
    sale_listing_input = [
        {
            "channelId": channel_id,
            "discountValue": sale_discount_value,
        }
    ]
    create_sale_channel_listing(
        e2e_staff_api_client,
        sale_id,
        add_channels=sale_listing_input,
    )
    catalogue_input = {"variants": [product_variant_id]}
    sale_catalogues_add(
        e2e_staff_api_client,
        sale_id,
        catalogue_input,
    )

    return sale_id, sale_discount_value


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
):
    voucher_data = create_voucher(
        e2e_staff_api_client,
        voucher_discount_type,
        voucher_code,
        "ENTIRE_ORDER",
    )
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
@pytest.mark.parametrize(
    "variant_price, sale_discount_value, sale_discount_type, expected_sale_discount, "
    "voucher_discount_value, voucher_discount_type, expected_voucher_discount, "
    "expected_unit_price",
    [
        ("19.99", 13, "PERCENTAGE", 2.60, 13, "PERCENTAGE", 2.26, 15.13),
        ("30", 10, "FIXED", 10, 5, "FIXED", 5, 17.5),
        ("56.50", 19.99, "FIXED", 19.99, 33, "PERCENTAGE", 12.05, 24.46),
        ("77.77", 17.5, "PERCENTAGE", 13.61, 25, "FIXED", 25, 51.66),
    ],
)
def test_checkout_calculate_discount_for_sale_and_voucher_1014(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    variant_price,
    sale_discount_value,
    sale_discount_type,
    expected_sale_discount,
    voucher_discount_value,
    voucher_discount_type,
    expected_voucher_discount,
    expected_unit_price,
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
        variant_price,
    )

    sale_id, sale_discount_value = prepare_sale_for_variant(
        e2e_staff_api_client,
        channel_id,
        product_variant_id,
        sale_discount_type,
        sale_discount_value,
    )

    voucher_discount_value, voucher_code = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        "VOUCHER001",
        voucher_discount_type,
        voucher_discount_value,
    )

    # Step 1 - Create checkout for product on sale
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
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
    unit_price_on_sale = round(float(product_variant_price - expected_sale_discount), 2)
    assert checkout_lines["unitPrice"]["gross"]["amount"] == unit_price_on_sale
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == product_variant_price

    # Step 2 Add voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )
    assert checkout_data["discount"]["amount"] == expected_voucher_discount
    assert checkout_data["lines"][0]["unitPrice"]["gross"]["amount"] == round(
        float(unit_price_on_sale - expected_voucher_discount), 2
    )

    # Step 3 Add variant to the checkout
    lines_add = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_lines_add(
        e2e_staff_api_client,
        checkout_id,
        lines_add,
    )
    checkout_lines = checkout_data["lines"][0]
    assert checkout_lines["quantity"] == 2
    assert checkout_lines["unitPrice"]["gross"]["amount"] == expected_unit_price
    subtotal_amount = expected_unit_price * 2
    assert checkout_lines["totalPrice"]["gross"]["amount"] == subtotal_amount

    # Step 4 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    total_gross_amount = round(subtotal_amount + shipping_price, 2)
    assert checkout_data["totalPrice"]["gross"]["amount"] == total_gross_amount

    # Step 5 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client, checkout_id, total_gross_amount
    )

    # Step 6 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == voucher_code

    order_line = order_data["lines"][0]
    assert order_line["unitDiscountType"] == "FIXED"
    assert order_line["unitPrice"]["gross"]["amount"] == expected_unit_price
    assert order_line["unitDiscountReason"] == f"Sale: {sale_id}"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["subtotal"]["gross"]["amount"] == subtotal_amount
    assert order_line["undiscountedUnitPrice"]["gross"]["amount"] == float(
        product_variant_price
    )
