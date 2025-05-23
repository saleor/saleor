import pytest

from .....product.tasks import recalculate_discounted_price_for_products_task
from ...product.utils.preparing_product import prepare_products
from ...sales.utils import create_sale, create_sale_channel_listing, sale_catalogues_add
from ...shop.utils import prepare_default_shop
from ...utils import assign_permissions
from ...vouchers.utils import create_voucher, create_voucher_channel_listing
from ..utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_lines_add,
    checkout_lines_delete,
    checkout_lines_update,
)


def prepare_sale_for_products(
    e2e_staff_api_client,
    channel_id,
    product_ids,
    sale_discount_type,
    sale_discount_value,
    sale_name,
):
    sale_name = sale_name
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
    catalogue_input = {"products": product_ids}
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
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": "ENTIRE_ORDER",
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


@pytest.mark.parametrize(
    ("legacy_discount_propagation", "entire_voucher_discount_reason"),
    [(True, "Entire order voucher code: VOUCHER001"), (False, "")],
)
@pytest.mark.e2e
def test_checkout_calculate_discount_for_percentage_sale_and_percentage_voucher_CORE_0114(
    legacy_discount_propagation,
    entire_voucher_discount_reason,
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

    shop_data = prepare_default_shop(
        e2e_staff_api_client,
        channel_order_settings={
            "useLegacyLineDiscountPropagation": legacy_discount_propagation
        },
    )
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    products_data = prepare_products(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        ["13.33", "16", "9.99", "20.5"],
    )
    product1_id = products_data[0]["product_id"]
    product1_variant_id = products_data[0]["variant_id"]
    product1_variant_price = float(products_data[0]["price"])

    product2_id = products_data[1]["product_id"]
    product2_variant_id = products_data[1]["variant_id"]
    product2_variant_price = float(products_data[1]["price"])

    product3_id = products_data[2]["product_id"]
    product3_variant_id = products_data[2]["variant_id"]
    product3_variant_price = float(products_data[2]["price"])

    product4_variant_id = products_data[3]["variant_id"]
    product4_variant_price = float(products_data[3]["price"])

    product_ids = [product1_id, product2_id, product3_id]

    sale_id, sale_discount_value = prepare_sale_for_products(
        e2e_staff_api_client,
        channel_id,
        product_ids,
        sale_discount_type="PERCENTAGE",
        sale_discount_value=13,
        sale_name="Sale_Percentage",
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    voucher_discount_value, voucher_code = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        "VOUCHER001",
        voucher_discount_type="PERCENTAGE",
        voucher_discount_value=13,
    )
    product1_quantity = 2
    product2_quantity = 3
    product3_quantity = 4
    product4_quantity = 1
    product2_new_quantity = 2
    product3_new_quantity = 3

    # Step 1 - checkoutCreate for product on sale
    lines = [
        {
            "variantId": product1_variant_id,
            "quantity": product1_quantity,
        },
        {
            "variantId": product2_variant_id,
            "quantity": product2_quantity,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]
    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]

    assert checkout_line1["variant"]["id"] == product1_variant_id
    assert checkout_line1["quantity"] == product1_quantity
    line1_discount = round(product1_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product1_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product1_variant_price
    assert checkout_line1["totalPrice"]["gross"]["amount"] == round(
        line1_unit_price * product1_quantity, 2
    )

    assert checkout_line2["variant"]["id"] == product2_variant_id
    assert checkout_line2["quantity"] == product2_quantity
    line2_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = product2_variant_price - line2_discount
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line2["totalPrice"]["gross"]["amount"] == round(
        line2_unit_price * product2_quantity, 2
    )

    calculated_subtotal = round(
        product1_quantity * line1_unit_price + product2_quantity * line2_unit_price, 2
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 2 - Add Lines
    lines = [
        {
            "variantId": product3_variant_id,
            "quantity": product3_quantity,
        },
        {
            "variantId": product4_variant_id,
            "quantity": product4_quantity,
        },
    ]
    checkout_data = checkout_lines_add(
        e2e_not_logged_api_client,
        checkout_id,
        lines,
    )
    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["variant"]["id"] == product3_variant_id
    assert checkout_line3["quantity"] == product3_quantity
    line3_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line3_unit_price = product3_variant_price - line3_discount
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert checkout_line3["totalPrice"]["gross"]["amount"] == round(
        line3_unit_price * product3_quantity, 2
    )

    checkout_line4 = checkout_data["lines"][3]
    assert checkout_line4["variant"]["id"] == product4_variant_id
    assert checkout_line4["quantity"] == 1
    line4_unit_price = product4_variant_price
    assert checkout_line4["unitPrice"]["gross"]["amount"] == line4_unit_price
    assert checkout_line4["undiscountedUnitPrice"]["amount"] == line4_unit_price
    assert checkout_line4["totalPrice"]["gross"]["amount"] == round(
        line4_unit_price * product4_quantity, 2
    )
    calculated_subtotal = round(
        product1_quantity * line1_unit_price
        + product2_quantity * line2_unit_price
        + product3_quantity * line3_unit_price
        + product4_quantity * line4_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 3 - Remove lines
    checkout_data = checkout_lines_delete(
        e2e_not_logged_api_client, checkout_id, linesIds=[checkout_line1["id"]]
    )
    assert len(checkout_data["lines"]) == 3
    assert checkout_data["lines"][0]["id"] == checkout_line2["id"]
    assert checkout_data["lines"][1]["id"] == checkout_line3["id"]
    assert checkout_data["lines"][2]["id"] == checkout_line4["id"]

    new_checkout_line1 = checkout_data["lines"][0]
    new_checkout_line2 = checkout_data["lines"][1]
    new_checkout_line3 = checkout_data["lines"][2]  # not on sale

    assert new_checkout_line1["variant"]["id"] == product2_variant_id
    assert new_checkout_line1["quantity"] == product2_quantity
    line1_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product2_variant_price - line1_discount
    assert new_checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert (
        new_checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    )
    assert new_checkout_line1["totalPrice"]["gross"]["amount"] == round(
        line1_unit_price * product2_quantity, 2
    )

    assert new_checkout_line2["variant"]["id"] == product3_variant_id
    assert new_checkout_line2["quantity"] == product3_quantity
    line2_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = round(product3_variant_price - line2_discount, 2)
    assert new_checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert (
        new_checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    )
    assert new_checkout_line2["totalPrice"]["gross"]["amount"] == round(
        line2_unit_price * product3_quantity, 2
    )

    assert new_checkout_line3["variant"]["id"] == product4_variant_id
    assert new_checkout_line3["quantity"] == 1
    line3_unit_price = product4_variant_price
    assert new_checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert new_checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    assert new_checkout_line3["totalPrice"]["gross"]["amount"] == round(
        line3_unit_price * product4_quantity, 2
    )

    calculated_subtotal = round(
        +product2_quantity * line1_unit_price
        + product3_quantity * line2_unit_price
        + product4_quantity * line3_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 4 - Update lines
    lines = [
        {
            "quantity": product2_new_quantity,
            "lineId": new_checkout_line1["id"],
        },
        {
            "quantity": product3_new_quantity,
            "lineId": new_checkout_line2["id"],
        },
    ]
    checkout_data = checkout_lines_update(e2e_not_logged_api_client, checkout_id, lines)
    checkout_data = checkout_data["checkout"]
    assert len(checkout_data["lines"]) == 3
    assert checkout_data["lines"][0]["id"] == checkout_line2["id"]
    assert checkout_data["lines"][1]["id"] == checkout_line3["id"]
    assert checkout_data["lines"][2]["id"] == checkout_line4["id"]

    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]
    checkout_line3 = checkout_data["lines"][2]  # not on sale

    assert checkout_line1["variant"]["id"] == product2_variant_id
    assert checkout_line1["quantity"] == product2_new_quantity
    line1_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product2_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    calculated_line1_total = round(product2_new_quantity * line1_unit_price, 2)
    assert checkout_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total

    assert checkout_line2["variant"]["id"] == product3_variant_id
    assert checkout_line2["quantity"] == product3_new_quantity
    line2_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = round(product3_variant_price - line2_discount, 2)
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    calculated_line2_total = round(product3_new_quantity * line2_unit_price, 2)
    assert checkout_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    assert checkout_line3["variant"]["id"] == product4_variant_id
    assert checkout_line3["quantity"] == product4_quantity
    line3_unit_price = product4_variant_price
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    calculated_line3_total = round(product4_quantity * line3_unit_price, 2)
    assert checkout_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total
    calculated_subtotal = round(
        +product2_new_quantity * line1_unit_price
        + product3_new_quantity * line2_unit_price
        + product4_quantity * line3_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 5 - Add voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )
    calculated_discount = round(calculated_subtotal * voucher_discount_value / 100, 2)
    assert checkout_data["discount"]["amount"] == calculated_discount
    assert checkout_data["voucherCode"] == voucher_code

    # Assert lines after voucher code
    assert len(checkout_data["lines"]) == 3
    checkout_line1 = checkout_data["lines"][0]
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line1["quantity"] == product2_new_quantity

    calculated_line1_discount = round(
        calculated_line1_total / calculated_subtotal * calculated_discount, 2
    )
    calculated_line1_total = round(
        calculated_line1_total - calculated_line1_discount, 2
    )
    assert checkout_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total

    checkout_line2 = checkout_data["lines"][1]
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert checkout_line2["quantity"] == product3_new_quantity

    calculated_line2_discount = round(
        calculated_line2_total / calculated_subtotal * calculated_discount, 2
    )
    calculated_line2_total = round(
        calculated_line2_total - calculated_line2_discount, 2
    )
    assert checkout_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product4_variant_price
    assert checkout_line3["quantity"] == product4_quantity

    calculated_line3_discount = round(
        calculated_discount - calculated_line1_discount - calculated_line2_discount, 2
    )
    calculated_line3_total = round(
        calculated_line3_total - calculated_line3_discount, 2
    )
    assert checkout_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total

    # Assert total and subtotal after voucher code
    calculated_subtotal = round(calculated_subtotal - calculated_discount, 2)
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    calculated_total = calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_total

    # Step 6 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    calculated_total = calculated_subtotal + shipping_price
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert total_gross_amount == calculated_total
    assert subtotal_gross_amount == calculated_subtotal

    # Step 7 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 8 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert len(order_data["lines"]) == 3
    order_line1 = order_data["lines"][0]
    order_line2 = order_data["lines"][1]
    order_line3 = order_data["lines"][2]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["subtotal"]["gross"]["amount"] == calculated_subtotal
    received_subtotal_from_lines = round(
        order_line1["totalPrice"]["gross"]["amount"]
        + order_line2["totalPrice"]["gross"]["amount"]
        + order_line3["totalPrice"]["gross"]["amount"],
        2,
    )

    assert order_data["subtotal"]["gross"]["amount"] == received_subtotal_from_lines
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price

    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["discounts"][0]["value"] == calculated_discount

    assert order_line1["quantity"] == product2_new_quantity
    assert entire_voucher_discount_reason in order_line1["unitDiscountReason"]
    assert f"Sale: {sale_id}" in order_line1["unitDiscountReason"]

    assert (
        order_line1["undiscountedUnitPrice"]["gross"]["amount"]
        == product2_variant_price
    )
    assert order_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total
    assert order_line1["unitPrice"]["gross"]["amount"] == round(
        calculated_line1_total / product2_new_quantity, 2
    )

    unit_discount1 = line1_discount
    unit_discount1 += (
        calculated_line1_discount / product2_new_quantity
        if legacy_discount_propagation
        else 0
    )
    assert order_line1["unitDiscount"]["amount"] == round(unit_discount1, 2)

    assert order_line2["quantity"] == product3_new_quantity

    assert entire_voucher_discount_reason in order_line2["unitDiscountReason"]
    assert f"Sale: {sale_id}" in order_line2["unitDiscountReason"]

    assert (
        order_line2["undiscountedUnitPrice"]["gross"]["amount"]
        == product3_variant_price
    )
    assert order_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total
    assert order_line2["unitPrice"]["gross"]["amount"] == round(
        calculated_line2_total / product3_new_quantity, 2
    )
    unit_discount2 = line2_discount
    unit_discount2 += (
        calculated_line2_discount / product3_new_quantity
        if legacy_discount_propagation
        else 0
    )
    assert order_line2["unitPrice"]["gross"]["amount"] == round(
        calculated_line2_total / product3_new_quantity, 2
    )

    assert order_line3["quantity"] == product4_quantity

    line_reason3 = order_line3["unitDiscountReason"] or ""
    assert entire_voucher_discount_reason in line_reason3

    assert (
        order_line3["undiscountedUnitPrice"]["gross"]["amount"]
        == product4_variant_price
    )
    assert order_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total
    assert order_line3["unitPrice"]["gross"]["amount"] == round(
        calculated_line3_total / product4_quantity, 2
    )
    unit_discount3 = 0
    unit_discount3 += calculated_line3_discount if legacy_discount_propagation else 0
    assert order_line3["unitDiscount"]["amount"] == unit_discount3


@pytest.mark.parametrize(
    ("legacy_discount_propagation", "entire_voucher_discount_reason"),
    [(True, "Entire order voucher code: VOUCHER002"), (False, "")],
)
@pytest.mark.e2e
def test_checkout_calculate_discount_for_fixed_sale_and_fixed_voucher_CORE_0114(
    legacy_discount_propagation,
    entire_voucher_discount_reason,
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

    shop_data = prepare_default_shop(
        e2e_staff_api_client,
        channel_order_settings={
            "useLegacyLineDiscountPropagation": legacy_discount_propagation
        },
    )
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    products_data = prepare_products(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        ["13.33", "16", "19.99", "20.5"],
    )
    product1_id = products_data[0]["product_id"]
    product1_variant_id = products_data[0]["variant_id"]
    product1_variant_price = float(products_data[0]["price"])

    product2_id = products_data[1]["product_id"]
    product2_variant_id = products_data[1]["variant_id"]
    product2_variant_price = float(products_data[1]["price"])

    product3_id = products_data[2]["product_id"]
    product3_variant_id = products_data[2]["variant_id"]
    product3_variant_price = float(products_data[2]["price"])

    product4_variant_id = products_data[3]["variant_id"]
    product4_variant_price = float(products_data[3]["price"])

    product_ids = [product1_id, product2_id, product3_id]

    sale_id, sale_discount_value = prepare_sale_for_products(
        e2e_staff_api_client,
        channel_id,
        product_ids,
        sale_discount_type="FIXED",
        sale_discount_value=10,
        sale_name="Sale_FIXED",
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    voucher_discount_value, voucher_code = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        "VOUCHER002",
        voucher_discount_type="FIXED",
        voucher_discount_value=5,
    )
    product1_quantity = 2
    product2_quantity = 3
    product3_quantity = 4
    product4_quantity = 1
    product2_new_quantity = 2
    product3_new_quantity = 3

    # Step 1 - checkoutCreate for product on sale
    lines = [
        {
            "variantId": product1_variant_id,
            "quantity": product1_quantity,
        },
        {
            "variantId": product2_variant_id,
            "quantity": product2_quantity,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]
    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]

    assert checkout_line1["variant"]["id"] == product1_variant_id
    assert checkout_line1["quantity"] == product1_quantity
    line1_discount = sale_discount_value
    line1_unit_price = product1_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product1_variant_price
    assert checkout_line1["totalPrice"]["gross"]["amount"] == round(
        line1_unit_price * product1_quantity, 2
    )

    assert checkout_line2["variant"]["id"] == product2_variant_id
    assert checkout_line2["quantity"] == product2_quantity
    line2_discount = sale_discount_value
    line2_unit_price = round(product2_variant_price - line2_discount, 2)
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line2["totalPrice"]["gross"]["amount"] == round(
        line2_unit_price * product2_quantity, 2
    )

    calculated_subtotal = round(
        product1_quantity * line1_unit_price + product2_quantity * line2_unit_price, 2
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 2 - Add Lines
    lines = [
        {
            "variantId": product3_variant_id,
            "quantity": product3_quantity,
        },
        {
            "variantId": product4_variant_id,
            "quantity": product4_quantity,
        },
    ]
    checkout_data = checkout_lines_add(
        e2e_not_logged_api_client,
        checkout_id,
        lines,
    )
    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["variant"]["id"] == product3_variant_id
    assert checkout_line3["quantity"] == product3_quantity
    line3_discount = sale_discount_value
    line3_unit_price = round(product3_variant_price - line3_discount, 2)
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert checkout_line3["totalPrice"]["gross"]["amount"] == round(
        line3_unit_price * product3_quantity, 2
    )

    checkout_line4 = checkout_data["lines"][3]
    assert checkout_line4["variant"]["id"] == product4_variant_id
    assert checkout_line4["quantity"] == 1
    line4_unit_price = product4_variant_price
    assert checkout_line4["unitPrice"]["gross"]["amount"] == line4_unit_price
    assert checkout_line4["undiscountedUnitPrice"]["amount"] == line4_unit_price
    assert checkout_line4["totalPrice"]["gross"]["amount"] == round(
        line4_unit_price * product4_quantity, 2
    )

    calculated_subtotal = round(
        product1_quantity * line1_unit_price
        + product2_quantity * line2_unit_price
        + product3_quantity * line3_unit_price
        + product4_quantity * line4_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 3 - Remove lines
    checkout_data = checkout_lines_delete(
        e2e_not_logged_api_client, checkout_id, linesIds=[checkout_line1["id"]]
    )
    assert len(checkout_data["lines"]) == 3
    assert checkout_data["lines"][0]["id"] == checkout_line2["id"]
    assert checkout_data["lines"][1]["id"] == checkout_line3["id"]
    assert checkout_data["lines"][2]["id"] == checkout_line4["id"]

    new_checkout_line1 = checkout_data["lines"][0]
    new_checkout_line2 = checkout_data["lines"][1]
    new_checkout_line3 = checkout_data["lines"][2]  # not on sale

    assert new_checkout_line1["variant"]["id"] == product2_variant_id
    assert new_checkout_line1["quantity"] == product2_quantity
    line1_discount = sale_discount_value
    line1_unit_price = product2_variant_price - line1_discount
    assert new_checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert (
        new_checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    )
    assert new_checkout_line1["totalPrice"]["gross"]["amount"] == round(
        line1_unit_price * product2_quantity, 2
    )

    assert new_checkout_line2["variant"]["id"] == product3_variant_id
    assert new_checkout_line2["quantity"] == product3_quantity
    line2_discount = sale_discount_value
    line2_unit_price = round(product3_variant_price - line2_discount, 2)
    assert new_checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert (
        new_checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    )
    assert new_checkout_line2["totalPrice"]["gross"]["amount"] == round(
        line2_unit_price * product3_quantity, 2
    )

    assert new_checkout_line3["variant"]["id"] == product4_variant_id
    assert new_checkout_line3["quantity"] == 1
    line3_unit_price = product4_variant_price
    assert new_checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert new_checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    assert new_checkout_line3["totalPrice"]["gross"]["amount"] == round(
        line3_unit_price * product4_quantity, 2
    )

    calculated_subtotal = round(
        +product2_quantity * line1_unit_price
        + product3_quantity * line2_unit_price
        + product4_quantity * line3_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 4 - Update lines
    lines = [
        {
            "quantity": product2_new_quantity,
            "lineId": new_checkout_line1["id"],
        },
        {
            "quantity": product3_new_quantity,
            "lineId": new_checkout_line2["id"],
        },
    ]
    checkout_data = checkout_lines_update(e2e_not_logged_api_client, checkout_id, lines)
    checkout_data = checkout_data["checkout"]
    assert len(checkout_data["lines"]) == 3
    assert checkout_data["lines"][0]["id"] == checkout_line2["id"]
    assert checkout_data["lines"][1]["id"] == checkout_line3["id"]
    assert checkout_data["lines"][2]["id"] == checkout_line4["id"]

    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]
    checkout_line3 = checkout_data["lines"][2]  # not on sale

    assert checkout_line1["variant"]["id"] == product2_variant_id
    assert checkout_line1["quantity"] == product2_new_quantity
    line1_discount = sale_discount_value
    line1_unit_price = product2_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    calculated_line1_total = round(product2_new_quantity * line1_unit_price, 2)
    assert checkout_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total

    assert checkout_line2["variant"]["id"] == product3_variant_id
    assert checkout_line2["quantity"] == product3_new_quantity
    line2_discount = sale_discount_value
    line2_unit_price = round(product3_variant_price - line2_discount, 2)
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    calculated_line2_total = round(product3_new_quantity * line2_unit_price, 2)
    assert checkout_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    assert checkout_line3["variant"]["id"] == product4_variant_id
    assert checkout_line3["quantity"] == product4_quantity
    line3_unit_price = product4_variant_price
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    calculated_line3_total = round(product4_quantity * line3_unit_price, 2)
    assert checkout_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total
    calculated_subtotal = round(
        +product2_new_quantity * line1_unit_price
        + product3_new_quantity * line2_unit_price
        + product4_quantity * line3_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 5 - Add voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )
    calculated_discount = voucher_discount_value
    assert checkout_data["discount"]["amount"] == calculated_discount
    assert checkout_data["voucherCode"] == voucher_code

    # Assert lines after voucher code
    assert len(checkout_data["lines"]) == 3
    checkout_line1 = checkout_data["lines"][0]
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line1["quantity"] == product2_new_quantity

    # jak dzielic discount na linie przy fixed voucher
    calculated_line1_discount = round(
        calculated_line1_total / calculated_subtotal * calculated_discount, 2
    )
    calculated_line1_total = round(
        calculated_line1_total - calculated_line1_discount, 2
    )
    assert checkout_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total

    checkout_line2 = checkout_data["lines"][1]
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert checkout_line2["quantity"] == product3_new_quantity

    calculated_line2_discount = round(
        calculated_line2_total / calculated_subtotal * calculated_discount, 2
    )
    calculated_line2_total = round(
        calculated_line2_total - calculated_line2_discount, 2
    )
    assert checkout_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product4_variant_price
    assert checkout_line3["quantity"] == product4_quantity

    calculated_line3_discount = round(
        calculated_discount - calculated_line1_discount - calculated_line2_discount, 2
    )
    calculated_line3_total = round(
        calculated_line3_total - calculated_line3_discount, 2
    )
    assert checkout_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total

    # Assert total and subtotal after voucher code
    calculated_subtotal = round(calculated_subtotal - calculated_discount, 2)
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    calculated_total = calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_total

    # Step 6 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    calculated_total = calculated_subtotal + shipping_price
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert total_gross_amount == calculated_total
    assert subtotal_gross_amount == calculated_subtotal

    # Step 7 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 8 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert len(order_data["lines"]) == 3
    order_line1 = order_data["lines"][0]
    order_line2 = order_data["lines"][1]
    order_line3 = order_data["lines"][2]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["subtotal"]["gross"]["amount"] == calculated_subtotal
    received_subtotal_from_lines = round(
        order_line1["totalPrice"]["gross"]["amount"]
        + order_line2["totalPrice"]["gross"]["amount"]
        + order_line3["totalPrice"]["gross"]["amount"],
        2,
    )

    assert order_data["subtotal"]["gross"]["amount"] == received_subtotal_from_lines
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price

    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["discounts"][0]["value"] == calculated_discount

    assert order_line1["quantity"] == product2_new_quantity
    assert entire_voucher_discount_reason in order_line1["unitDiscountReason"]
    assert f"Sale: {sale_id}" in order_line1["unitDiscountReason"]

    assert (
        order_line1["undiscountedUnitPrice"]["gross"]["amount"]
        == product2_variant_price
    )
    assert order_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total
    assert order_line1["unitPrice"]["gross"]["amount"] == round(
        calculated_line1_total / product2_new_quantity, 2
    )

    unit_discount1 = line1_discount
    unit_discount1 += (
        calculated_line1_discount / product2_new_quantity
        if legacy_discount_propagation
        else 0
    )
    assert order_line1["unitDiscount"]["amount"] == round(unit_discount1, 2)

    assert order_line2["quantity"] == product3_new_quantity

    assert entire_voucher_discount_reason in order_line2["unitDiscountReason"]
    assert f"Sale: {sale_id}" in order_line2["unitDiscountReason"]

    assert (
        order_line2["undiscountedUnitPrice"]["gross"]["amount"]
        == product3_variant_price
    )
    assert order_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total
    assert order_line2["unitPrice"]["gross"]["amount"] == round(
        calculated_line2_total / product3_new_quantity, 2
    )
    unit_discount2 = line2_discount
    unit_discount2 += (
        calculated_line2_discount / product3_new_quantity
        if legacy_discount_propagation
        else 0
    )
    assert order_line2["unitDiscount"]["amount"] == round(unit_discount2, 2)

    assert order_line3["quantity"] == product4_quantity

    line_reason3 = order_line3["unitDiscountReason"] or ""
    assert entire_voucher_discount_reason in line_reason3

    assert (
        order_line3["undiscountedUnitPrice"]["gross"]["amount"]
        == product4_variant_price
    )
    assert order_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total
    assert order_line3["unitPrice"]["gross"]["amount"] == round(
        calculated_line3_total / product4_quantity, 2
    )
    unit_discount3 = 0
    unit_discount3 += calculated_line3_discount if legacy_discount_propagation else 0
    assert order_line3["unitDiscount"]["amount"] == unit_discount3


@pytest.mark.parametrize(
    ("legacy_discount_propagation", "entire_voucher_discount_reason"),
    [(True, "Entire order voucher code: VOUCHER003"), (False, "")],
)
@pytest.mark.e2e
def test_checkout_calculate_discount_for_fixed_sale_and_percentage_voucher_CORE_0114(
    legacy_discount_propagation,
    entire_voucher_discount_reason,
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

    shop_data = prepare_default_shop(
        e2e_staff_api_client,
        channel_order_settings={
            "useLegacyLineDiscountPropagation": legacy_discount_propagation
        },
    )
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    products_data = prepare_products(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        ["13.33", "16", "9.99", "20.5"],
    )
    product1_id = products_data[0]["product_id"]
    product1_variant_id = products_data[0]["variant_id"]
    product1_variant_price = float(products_data[0]["price"])

    product2_id = products_data[1]["product_id"]
    product2_variant_id = products_data[1]["variant_id"]
    product2_variant_price = float(products_data[1]["price"])

    product3_id = products_data[2]["product_id"]
    product3_variant_id = products_data[2]["variant_id"]
    product3_variant_price = float(products_data[2]["price"])

    product4_variant_id = products_data[3]["variant_id"]
    product4_variant_price = float(products_data[3]["price"])

    product_ids = [product1_id, product2_id, product3_id]

    sale_id, sale_discount_value = prepare_sale_for_products(
        e2e_staff_api_client,
        channel_id,
        product_ids,
        sale_discount_type="FIXED",
        sale_discount_value=5,
        sale_name="Sale_fixed",
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    voucher_discount_value, voucher_code = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        "VOUCHER003",
        voucher_discount_type="PERCENTAGE",
        voucher_discount_value=15,
    )
    product1_quantity = 2
    product2_quantity = 3
    product3_quantity = 4
    product4_quantity = 1
    product2_new_quantity = 2
    product3_new_quantity = 3

    # Step 1 - checkoutCreate for product on sale
    lines = [
        {
            "variantId": product1_variant_id,
            "quantity": product1_quantity,
        },
        {
            "variantId": product2_variant_id,
            "quantity": product2_quantity,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]
    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]

    assert checkout_line1["variant"]["id"] == product1_variant_id
    assert checkout_line1["quantity"] == product1_quantity
    line1_discount = sale_discount_value
    line1_unit_price = product1_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product1_variant_price
    assert checkout_line1["totalPrice"]["gross"]["amount"] == round(
        line1_unit_price * product1_quantity, 2
    )

    assert checkout_line2["variant"]["id"] == product2_variant_id
    assert checkout_line2["quantity"] == product2_quantity
    line2_discount = sale_discount_value
    line2_unit_price = product2_variant_price - line2_discount
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line2["totalPrice"]["gross"]["amount"] == round(
        line2_unit_price * product2_quantity, 2
    )

    calculated_subtotal = round(
        product1_quantity * line1_unit_price + product2_quantity * line2_unit_price, 2
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 2 - Add Lines
    lines = [
        {
            "variantId": product3_variant_id,
            "quantity": product3_quantity,
        },
        {
            "variantId": product4_variant_id,
            "quantity": product4_quantity,
        },
    ]
    checkout_data = checkout_lines_add(
        e2e_not_logged_api_client,
        checkout_id,
        lines,
    )
    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["variant"]["id"] == product3_variant_id
    assert checkout_line3["quantity"] == product3_quantity
    line3_discount = sale_discount_value
    line3_unit_price = product3_variant_price - line3_discount
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert checkout_line3["totalPrice"]["gross"]["amount"] == round(
        line3_unit_price * product3_quantity, 2
    )

    checkout_line4 = checkout_data["lines"][3]
    assert checkout_line4["variant"]["id"] == product4_variant_id
    assert checkout_line4["quantity"] == 1
    line4_unit_price = product4_variant_price
    assert checkout_line4["unitPrice"]["gross"]["amount"] == line4_unit_price
    assert checkout_line4["undiscountedUnitPrice"]["amount"] == line4_unit_price
    assert checkout_line4["totalPrice"]["gross"]["amount"] == round(
        line4_unit_price * product4_quantity, 2
    )

    calculated_subtotal = round(
        product1_quantity * line1_unit_price
        + product2_quantity * line2_unit_price
        + product3_quantity * line3_unit_price
        + product4_quantity * line4_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 3 - Remove lines
    checkout_data = checkout_lines_delete(
        e2e_not_logged_api_client, checkout_id, linesIds=[checkout_line1["id"]]
    )
    assert len(checkout_data["lines"]) == 3
    assert checkout_data["lines"][0]["id"] == checkout_line2["id"]
    assert checkout_data["lines"][1]["id"] == checkout_line3["id"]
    assert checkout_data["lines"][2]["id"] == checkout_line4["id"]

    new_checkout_line1 = checkout_data["lines"][0]
    new_checkout_line2 = checkout_data["lines"][1]
    new_checkout_line3 = checkout_data["lines"][2]  # not on sale

    assert new_checkout_line1["variant"]["id"] == product2_variant_id
    assert new_checkout_line1["quantity"] == product2_quantity
    line1_discount = sale_discount_value
    line1_unit_price = product2_variant_price - line1_discount
    assert new_checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert (
        new_checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    )
    assert new_checkout_line1["totalPrice"]["gross"]["amount"] == round(
        line1_unit_price * product2_quantity, 2
    )

    assert new_checkout_line2["variant"]["id"] == product3_variant_id
    assert new_checkout_line2["quantity"] == product3_quantity
    line2_discount = sale_discount_value
    line2_unit_price = round(product3_variant_price - line2_discount, 2)
    assert new_checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert (
        new_checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    )
    assert new_checkout_line2["totalPrice"]["gross"]["amount"] == round(
        line2_unit_price * product3_quantity, 2
    )

    assert new_checkout_line3["variant"]["id"] == product4_variant_id
    assert new_checkout_line3["quantity"] == 1
    line3_unit_price = product4_variant_price
    assert new_checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert new_checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    assert new_checkout_line3["totalPrice"]["gross"]["amount"] == round(
        line3_unit_price * product4_quantity, 2
    )

    calculated_subtotal = round(
        +product2_quantity * line1_unit_price
        + product3_quantity * line2_unit_price
        + product4_quantity * line3_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 4 - Update lines
    lines = [
        {
            "quantity": product2_new_quantity,
            "lineId": new_checkout_line1["id"],
        },
        {
            "quantity": product3_new_quantity,
            "lineId": new_checkout_line2["id"],
        },
    ]
    checkout_data = checkout_lines_update(e2e_not_logged_api_client, checkout_id, lines)
    checkout_data = checkout_data["checkout"]
    assert len(checkout_data["lines"]) == 3
    assert checkout_data["lines"][0]["id"] == checkout_line2["id"]
    assert checkout_data["lines"][1]["id"] == checkout_line3["id"]
    assert checkout_data["lines"][2]["id"] == checkout_line4["id"]

    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]
    checkout_line3 = checkout_data["lines"][2]  # not on sale

    assert checkout_line1["variant"]["id"] == product2_variant_id
    assert checkout_line1["quantity"] == product2_new_quantity
    line1_discount = sale_discount_value
    line1_unit_price = product2_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    calculated_line1_total = round(product2_new_quantity * line1_unit_price, 2)
    assert checkout_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total

    assert checkout_line2["variant"]["id"] == product3_variant_id
    assert checkout_line2["quantity"] == product3_new_quantity
    line2_discount = sale_discount_value
    line2_unit_price = round(product3_variant_price - line2_discount, 2)
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    calculated_line2_total = round(product3_new_quantity * line2_unit_price, 2)
    assert checkout_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    assert checkout_line3["variant"]["id"] == product4_variant_id
    assert checkout_line3["quantity"] == product4_quantity
    line3_unit_price = product4_variant_price
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    calculated_line3_total = round(product4_quantity * line3_unit_price, 2)
    assert checkout_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total
    calculated_subtotal = round(
        +product2_new_quantity * line1_unit_price
        + product3_new_quantity * line2_unit_price
        + product4_quantity * line3_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 5 - Add voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )
    calculated_discount = round(calculated_subtotal * voucher_discount_value / 100, 2)
    assert checkout_data["discount"]["amount"] == calculated_discount
    assert checkout_data["voucherCode"] == voucher_code

    # Assert lines after voucher code
    assert len(checkout_data["lines"]) == 3
    checkout_line1 = checkout_data["lines"][0]
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line1["quantity"] == product2_new_quantity

    calculated_line1_discount = round(
        calculated_line1_total / calculated_subtotal * calculated_discount, 2
    )
    calculated_line1_total = round(
        calculated_line1_total - calculated_line1_discount, 2
    )
    assert checkout_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total

    checkout_line2 = checkout_data["lines"][1]
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert checkout_line2["quantity"] == product3_new_quantity

    calculated_line2_discount = round(
        calculated_line2_total / calculated_subtotal * calculated_discount, 2
    )
    calculated_line2_total = round(
        calculated_line2_total - calculated_line2_discount, 2
    )
    assert checkout_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product4_variant_price
    assert checkout_line3["quantity"] == product4_quantity

    calculated_line3_discount = round(
        calculated_discount - calculated_line1_discount - calculated_line2_discount, 2
    )
    calculated_line3_total = round(
        calculated_line3_total - calculated_line3_discount, 2
    )
    assert checkout_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total

    # Assert total and subtotal after voucher code
    calculated_subtotal = round(calculated_subtotal - calculated_discount, 2)
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    calculated_total = calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_total

    # Step 6 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    calculated_total = calculated_subtotal + shipping_price
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert total_gross_amount == calculated_total
    assert subtotal_gross_amount == calculated_subtotal

    # Step 7 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 8 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert len(order_data["lines"]) == 3
    order_line1 = order_data["lines"][0]
    order_line2 = order_data["lines"][1]
    order_line3 = order_data["lines"][2]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["subtotal"]["gross"]["amount"] == calculated_subtotal
    received_subtotal_from_lines = round(
        order_line1["totalPrice"]["gross"]["amount"]
        + order_line2["totalPrice"]["gross"]["amount"]
        + order_line3["totalPrice"]["gross"]["amount"],
        2,
    )

    assert order_data["subtotal"]["gross"]["amount"] == received_subtotal_from_lines
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price

    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["discounts"][0]["value"] == calculated_discount

    assert order_line1["quantity"] == product2_new_quantity
    assert entire_voucher_discount_reason in order_line1["unitDiscountReason"]
    assert f"Sale: {sale_id}" in order_line1["unitDiscountReason"]

    assert (
        order_line1["undiscountedUnitPrice"]["gross"]["amount"]
        == product2_variant_price
    )
    assert order_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total
    assert order_line1["unitPrice"]["gross"]["amount"] == round(
        calculated_line1_total / product2_new_quantity, 2
    )
    unit_discount1 = line1_discount
    unit_discount1 += (
        calculated_line1_discount / product2_new_quantity
        if legacy_discount_propagation
        else 0
    )
    assert order_line1["unitDiscount"]["amount"] == round(unit_discount1, 2)
    assert order_line2["quantity"] == product3_new_quantity

    assert entire_voucher_discount_reason in order_line2["unitDiscountReason"]
    assert f"Sale: {sale_id}" in order_line2["unitDiscountReason"]

    assert (
        order_line2["undiscountedUnitPrice"]["gross"]["amount"]
        == product3_variant_price
    )
    assert order_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    assert order_line2["unitPrice"]["gross"]["amount"] == round(
        calculated_line2_total / product3_new_quantity, 2
    )
    unit_discount2 = line2_discount
    unit_discount2 += (
        calculated_line2_discount / product3_new_quantity
        if legacy_discount_propagation
        else 0
    )
    assert order_line2["unitDiscount"]["amount"] == round(unit_discount2, 2)

    assert order_line3["quantity"] == product4_quantity
    line_reason3 = order_line3["unitDiscountReason"] or ""
    assert entire_voucher_discount_reason in line_reason3

    assert (
        order_line3["undiscountedUnitPrice"]["gross"]["amount"]
        == product4_variant_price
    )
    assert order_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total
    assert order_line3["unitPrice"]["gross"]["amount"] == round(
        calculated_line3_total / product4_quantity, 2
    )
    unit_discount3 = 0
    unit_discount3 += calculated_line3_discount if legacy_discount_propagation else 0
    assert order_line3["unitDiscount"]["amount"] == unit_discount3


@pytest.mark.parametrize(
    ("legacy_discount_propagation", "entire_voucher_discount_reason"),
    [(True, "Entire order voucher code: VOUCHER004"), (False, "")],
)
@pytest.mark.e2e
def test_checkout_calculate_discount_for_percentage_sale_and_fixed_voucher_CORE_0114(
    legacy_discount_propagation,
    entire_voucher_discount_reason,
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

    shop_data = prepare_default_shop(
        e2e_staff_api_client,
        channel_order_settings={
            "useLegacyLineDiscountPropagation": legacy_discount_propagation
        },
    )
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    products_data = prepare_products(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        ["13.33", "16", "9.99", "20.5"],
    )
    product1_id = products_data[0]["product_id"]
    product1_variant_id = products_data[0]["variant_id"]
    product1_variant_price = float(products_data[0]["price"])

    product2_id = products_data[1]["product_id"]
    product2_variant_id = products_data[1]["variant_id"]
    product2_variant_price = float(products_data[1]["price"])

    product3_id = products_data[2]["product_id"]
    product3_variant_id = products_data[2]["variant_id"]
    product3_variant_price = float(products_data[2]["price"])

    product4_variant_id = products_data[3]["variant_id"]
    product4_variant_price = float(products_data[3]["price"])

    product_ids = [product1_id, product2_id, product3_id]

    sale_id, sale_discount_value = prepare_sale_for_products(
        e2e_staff_api_client,
        channel_id,
        product_ids,
        sale_discount_type="PERCENTAGE",
        sale_discount_value=20,
        sale_name="Sale_Percentage",
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    voucher_discount_value, voucher_code = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        "VOUCHER004",
        voucher_discount_type="FIXED",
        voucher_discount_value=3,
    )
    product1_quantity = 2
    product2_quantity = 3
    product3_quantity = 4
    product4_quantity = 1
    product2_new_quantity = 2
    product3_new_quantity = 3

    # Step 1 - checkoutCreate for product on sale
    lines = [
        {
            "variantId": product1_variant_id,
            "quantity": product1_quantity,
        },
        {
            "variantId": product2_variant_id,
            "quantity": product2_quantity,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]
    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]

    assert checkout_line1["variant"]["id"] == product1_variant_id
    assert checkout_line1["quantity"] == product1_quantity
    line1_discount = round(product1_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product1_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product1_variant_price
    assert checkout_line1["totalPrice"]["gross"]["amount"] == round(
        line1_unit_price * product1_quantity, 2
    )

    assert checkout_line2["variant"]["id"] == product2_variant_id
    assert checkout_line2["quantity"] == product2_quantity
    line2_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = product2_variant_price - line2_discount
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line2["totalPrice"]["gross"]["amount"] == round(
        line2_unit_price * product2_quantity, 2
    )

    calculated_subtotal = round(
        product1_quantity * line1_unit_price + product2_quantity * line2_unit_price, 2
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 2 - Add Lines
    lines = [
        {
            "variantId": product3_variant_id,
            "quantity": product3_quantity,
        },
        {
            "variantId": product4_variant_id,
            "quantity": product4_quantity,
        },
    ]
    checkout_data = checkout_lines_add(
        e2e_not_logged_api_client,
        checkout_id,
        lines,
    )
    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["variant"]["id"] == product3_variant_id
    assert checkout_line3["quantity"] == product3_quantity
    line3_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line3_unit_price = product3_variant_price - line3_discount
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert checkout_line3["totalPrice"]["gross"]["amount"] == round(
        line3_unit_price * product3_quantity, 2
    )

    checkout_line4 = checkout_data["lines"][3]
    assert checkout_line4["variant"]["id"] == product4_variant_id
    assert checkout_line4["quantity"] == 1
    line4_unit_price = product4_variant_price
    assert checkout_line4["unitPrice"]["gross"]["amount"] == line4_unit_price
    assert checkout_line4["undiscountedUnitPrice"]["amount"] == line4_unit_price
    assert checkout_line4["totalPrice"]["gross"]["amount"] == round(
        line4_unit_price * product4_quantity, 2
    )

    calculated_subtotal = round(
        product1_quantity * line1_unit_price
        + product2_quantity * line2_unit_price
        + product3_quantity * line3_unit_price
        + product4_quantity * line4_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 3 - Remove lines
    checkout_data = checkout_lines_delete(
        e2e_not_logged_api_client, checkout_id, linesIds=[checkout_line1["id"]]
    )
    assert len(checkout_data["lines"]) == 3
    assert checkout_data["lines"][0]["id"] == checkout_line2["id"]
    assert checkout_data["lines"][1]["id"] == checkout_line3["id"]
    assert checkout_data["lines"][2]["id"] == checkout_line4["id"]

    new_checkout_line1 = checkout_data["lines"][0]
    new_checkout_line2 = checkout_data["lines"][1]
    new_checkout_line3 = checkout_data["lines"][2]  # not on sale

    assert new_checkout_line1["variant"]["id"] == product2_variant_id
    assert new_checkout_line1["quantity"] == product2_quantity
    line1_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product2_variant_price - line1_discount
    assert new_checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert (
        new_checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    )
    assert new_checkout_line1["totalPrice"]["gross"]["amount"] == round(
        line1_unit_price * product2_quantity, 2
    )

    assert new_checkout_line2["variant"]["id"] == product3_variant_id
    assert new_checkout_line2["quantity"] == product3_quantity
    line2_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = round(product3_variant_price - line2_discount, 2)
    assert new_checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert (
        new_checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    )
    assert new_checkout_line2["totalPrice"]["gross"]["amount"] == round(
        line2_unit_price * product3_quantity, 2
    )

    assert new_checkout_line3["variant"]["id"] == product4_variant_id
    assert new_checkout_line3["quantity"] == 1
    line3_unit_price = product4_variant_price
    assert new_checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert new_checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    assert new_checkout_line3["totalPrice"]["gross"]["amount"] == round(
        line3_unit_price * product4_quantity, 2
    )

    calculated_subtotal = round(
        +product2_quantity * line1_unit_price
        + product3_quantity * line2_unit_price
        + product4_quantity * line3_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 4 - Update lines
    lines = [
        {
            "quantity": product2_new_quantity,
            "lineId": new_checkout_line1["id"],
        },
        {
            "quantity": product3_new_quantity,
            "lineId": new_checkout_line2["id"],
        },
    ]
    checkout_data = checkout_lines_update(e2e_not_logged_api_client, checkout_id, lines)
    checkout_data = checkout_data["checkout"]
    assert len(checkout_data["lines"]) == 3
    assert checkout_data["lines"][0]["id"] == checkout_line2["id"]
    assert checkout_data["lines"][1]["id"] == checkout_line3["id"]
    assert checkout_data["lines"][2]["id"] == checkout_line4["id"]

    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]
    checkout_line3 = checkout_data["lines"][2]  # not on sale

    assert checkout_line1["variant"]["id"] == product2_variant_id
    assert checkout_line1["quantity"] == product2_new_quantity
    line1_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product2_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    calculated_line1_total = round(product2_new_quantity * line1_unit_price, 2)
    assert checkout_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total

    assert checkout_line2["variant"]["id"] == product3_variant_id
    assert checkout_line2["quantity"] == product3_new_quantity
    line2_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = round(product3_variant_price - line2_discount, 2)
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    calculated_line2_total = round(product3_new_quantity * line2_unit_price, 2)
    assert checkout_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    assert checkout_line3["variant"]["id"] == product4_variant_id
    assert checkout_line3["quantity"] == product4_quantity
    line3_unit_price = product4_variant_price
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    calculated_line3_total = round(product4_quantity * line3_unit_price, 2)
    assert checkout_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total
    calculated_subtotal = round(
        +product2_new_quantity * line1_unit_price
        + product3_new_quantity * line2_unit_price
        + product4_quantity * line3_unit_price,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 5 - Add voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )
    calculated_discount = voucher_discount_value
    assert checkout_data["discount"]["amount"] == calculated_discount
    assert checkout_data["voucherCode"] == voucher_code

    # Assert lines after voucher code
    assert len(checkout_data["lines"]) == 3
    checkout_line1 = checkout_data["lines"][0]
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line1["quantity"] == product2_new_quantity

    calculated_line1_discount = round(
        calculated_line1_total / calculated_subtotal * calculated_discount, 2
    )
    calculated_line1_total = round(
        calculated_line1_total - calculated_line1_discount, 2
    )
    assert checkout_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total

    checkout_line2 = checkout_data["lines"][1]
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert checkout_line2["quantity"] == product3_new_quantity

    calculated_line2_discount = round(
        calculated_line2_total / calculated_subtotal * calculated_discount, 2
    )
    calculated_line2_total = round(
        calculated_line2_total - calculated_line2_discount, 2
    )
    assert checkout_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total

    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product4_variant_price
    assert checkout_line3["quantity"] == product4_quantity

    calculated_line3_discount = round(
        calculated_discount - calculated_line1_discount - calculated_line2_discount, 2
    )
    calculated_line3_total = round(
        calculated_line3_total - calculated_line3_discount, 2
    )
    assert checkout_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total

    # Assert total and subtotal after voucher code
    calculated_subtotal = round(calculated_subtotal - calculated_discount, 2)
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    calculated_total = calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_total

    # Step 6 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    calculated_total = calculated_subtotal + shipping_price
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert total_gross_amount == calculated_total
    assert subtotal_gross_amount == calculated_subtotal

    # Step 7 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 8 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert len(order_data["lines"]) == 3
    order_line1 = order_data["lines"][0]
    order_line2 = order_data["lines"][1]
    order_line3 = order_data["lines"][2]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["subtotal"]["gross"]["amount"] == calculated_subtotal
    received_subtotal_from_lines = round(
        order_line1["totalPrice"]["gross"]["amount"]
        + order_line2["totalPrice"]["gross"]["amount"]
        + order_line3["totalPrice"]["gross"]["amount"],
        2,
    )

    assert order_data["subtotal"]["gross"]["amount"] == received_subtotal_from_lines
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price

    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == voucher_code
    assert order_data["discounts"][0]["value"] == calculated_discount

    assert order_line1["quantity"] == product2_new_quantity

    assert entire_voucher_discount_reason in order_line1["unitDiscountReason"]
    assert f"Sale: {sale_id}" in order_line1["unitDiscountReason"]

    assert (
        order_line1["undiscountedUnitPrice"]["gross"]["amount"]
        == product2_variant_price
    )
    assert order_line1["totalPrice"]["gross"]["amount"] == calculated_line1_total
    assert order_line1["unitPrice"]["gross"]["amount"] == round(
        calculated_line1_total / product2_new_quantity, 2
    )
    unit_discount1 = line1_discount
    unit_discount1 += (
        calculated_line1_discount / product2_new_quantity
        if legacy_discount_propagation
        else 0
    )
    assert order_line1["unitDiscount"]["amount"] == round(unit_discount1, 2)
    assert order_line2["quantity"] == product3_new_quantity

    assert entire_voucher_discount_reason in order_line2["unitDiscountReason"]
    assert f"Sale: {sale_id}" in order_line2["unitDiscountReason"]

    assert (
        order_line2["undiscountedUnitPrice"]["gross"]["amount"]
        == product3_variant_price
    )
    assert order_line2["totalPrice"]["gross"]["amount"] == calculated_line2_total
    assert order_line2["unitPrice"]["gross"]["amount"] == round(
        calculated_line2_total / product3_new_quantity, 2
    )

    unit_discount2 = line2_discount
    unit_discount2 += (
        calculated_line2_discount / product3_new_quantity
        if legacy_discount_propagation
        else 0
    )
    assert order_line2["unitDiscount"]["amount"] == round(unit_discount2, 2)

    assert order_line3["quantity"] == product4_quantity

    line_reason3 = order_line3["unitDiscountReason"] or ""
    assert entire_voucher_discount_reason in line_reason3

    assert (
        order_line3["undiscountedUnitPrice"]["gross"]["amount"]
        == product4_variant_price
    )
    assert order_line3["totalPrice"]["gross"]["amount"] == calculated_line3_total
    assert order_line3["unitPrice"]["gross"]["amount"] == round(
        calculated_line3_total / product4_quantity, 2
    )
    unit_discount3 = 0
    unit_discount3 += calculated_line3_discount if legacy_discount_propagation else 0
    assert order_line3["unitDiscount"]["amount"] == unit_discount3
