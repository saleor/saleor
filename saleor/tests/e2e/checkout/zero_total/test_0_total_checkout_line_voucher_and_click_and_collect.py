import pytest

from ...channel.utils import update_channel
from ...product.utils.preparing_product import prepare_products
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
from ...vouchers.utils.prepare_voucher import prepare_voucher
from ...warehouse.utils import update_warehouse
from ..utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_lines_add,
)


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("mark_as_paid_strategy"),
    [
        ("TRANSACTION_FLOW"),
        ("PAYMENT_FLOW"),
    ],
)
def test_complete_0_total_checkout_with_lines_voucher_and_click_and_collect_CORE_0125(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
    permission_manage_discounts,
    mark_as_paid_strategy,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        *shop_permissions,
        permission_manage_discounts,
    ]

    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    update_warehouse(
        e2e_staff_api_client,
        warehouse_id,
        is_private=False,
        click_and_collect_option="LOCAL",
    )
    update_channel(
        e2e_staff_api_client,
        channel_id,
        input={"orderSettings": {"markAsPaidStrategy": mark_as_paid_strategy}},
    )
    products_data = prepare_products(
        e2e_staff_api_client, warehouse_id, channel_id, [9.99, 150, 77.77]
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

    product1_quantity = 1
    product2_quantity = 4
    product3_quantity = 2

    voucher_code, _voucher_id, _voucher_discount_value = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="voucher_qwerty",
        voucher_discount_type="PERCENTAGE",
        voucher_discount_value=100,
        voucher_type="SPECIFIC_PRODUCT",
        products_list=[product1_id, product2_id, product3_id],
        apply_once_per_order=False,
    )
    # Step 1 - Create checkout for products
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
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]
    line1_total = round(product1_variant_price * product1_quantity, 2)
    line2_total = round(product2_variant_price * product2_quantity, 2)
    calculated_subtotal = round(line1_total + line2_total, 2)

    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal
    line1 = checkout_data["lines"][0]
    assert line1["unitPrice"]["gross"]["amount"] == product1_variant_price
    assert line1["totalPrice"]["gross"]["amount"] == line1_total
    assert line1["undiscountedTotalPrice"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["amount"] == product1_variant_price

    line2 = checkout_data["lines"][1]
    assert line2["unitPrice"]["gross"]["amount"] == product2_variant_price
    assert line2["totalPrice"]["gross"]["amount"] == line2_total
    assert line2["undiscountedTotalPrice"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["amount"] == product2_variant_price

    # Step 2 - Add more lines
    lines = [
        {
            "variantId": product3_variant_id,
            "quantity": product3_quantity,
        }
    ]
    checkout_data = checkout_lines_add(e2e_not_logged_api_client, checkout_id, lines)
    assert checkout_data["isShippingRequired"] is True
    line3_total = round(product3_variant_price * product3_quantity, 2)
    calculated_subtotal = round(line1_total + line2_total + line3_total, 2)

    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal

    collection_point = checkout_data["availableCollectionPoints"][0]
    assert collection_point["id"] == warehouse_id

    line3 = checkout_data["lines"][2]
    assert line3["unitPrice"]["gross"]["amount"] == product3_variant_price
    assert line3["totalPrice"]["gross"]["amount"] == line3_total
    assert line3["undiscountedTotalPrice"]["amount"] == line3_total
    assert line3["undiscountedUnitPrice"]["amount"] == product3_variant_price

    # Step 3 - Assign delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        collection_point["id"],
    )
    assert checkout_data["deliveryMethod"]["id"] == warehouse_id
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["shippingPrice"]["gross"]["amount"] == 0

    # Step 4 - Add voucher code to the checkout
    data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    assert data["voucherCode"] == voucher_code
    assert data["totalPrice"]["gross"]["amount"] == 0
    assert data["subtotalPrice"]["gross"]["amount"] == 0
    assert data["shippingPrice"]["gross"]["amount"] == 0

    assert len(data["lines"]) == 3
    line1 = data["lines"][0]
    assert line1["unitPrice"]["gross"]["amount"] == 0
    assert line1["totalPrice"]["gross"]["amount"] == 0
    assert line1["undiscountedTotalPrice"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["amount"] == product1_variant_price

    line2 = data["lines"][1]
    assert line2["unitPrice"]["gross"]["amount"] == 0
    assert line2["totalPrice"]["gross"]["amount"] == 0
    assert line2["undiscountedTotalPrice"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["amount"] == product2_variant_price

    line3 = data["lines"][2]
    assert line3["unitPrice"]["gross"]["amount"] == 0
    assert line3["totalPrice"]["gross"]["amount"] == 0
    assert line3["undiscountedTotalPrice"]["amount"] == line3_total
    assert line3["undiscountedUnitPrice"]["amount"] == product3_variant_price

    # Step 5 - Complete checkout and verify created order
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNCONFIRMED"
    assert order_data["deliveryMethod"]["id"] == warehouse_id
    assert order_data["total"]["gross"]["amount"] == 0
    assert order_data["subtotal"]["gross"]["amount"] == 0
    assert order_data["shippingPrice"]["gross"]["amount"] == 0

    assert len(order_data["lines"]) == 3
    line1 = order_data["lines"][0]
    assert line1["unitPrice"]["gross"]["amount"] == 0
    assert line1["totalPrice"]["gross"]["amount"] == 0
    assert line1["undiscountedTotalPrice"]["gross"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["gross"]["amount"] == product1_variant_price

    line2 = order_data["lines"][1]
    assert line2["unitPrice"]["gross"]["amount"] == 0
    assert line2["totalPrice"]["gross"]["amount"] == 0
    assert line2["undiscountedTotalPrice"]["gross"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["gross"]["amount"] == product2_variant_price

    line3 = order_data["lines"][2]
    assert line3["unitPrice"]["gross"]["amount"] == 0
    assert line3["totalPrice"]["gross"]["amount"] == 0
    assert line3["undiscountedTotalPrice"]["gross"]["amount"] == line3_total
    assert line3["undiscountedUnitPrice"]["gross"]["amount"] == product3_variant_price
