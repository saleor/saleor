import pytest

from ......product.tasks import recalculate_discounted_price_for_products_task
from ....product.utils import get_product
from ....product.utils.preparing_product import prepare_products
from ....sales.utils import (
    create_sale,
    create_sale_channel_listing,
    sale_catalogues_add,
)
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ...utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_lines_add,
    checkout_lines_update,
)


def prepare_sale_for_products(
    e2e_staff_api_client,
    channel_id,
    product_ids,
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
    catalogue_input = {"products": product_ids}
    sale_catalogues_add(
        e2e_staff_api_client,
        sale_id,
        catalogue_input,
    )

    return sale_id


@pytest.mark.e2e
def test_checkout_with_fixed_sale_should_not_result_in_negative_price_CORE_1005(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    products_data = prepare_products(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        prices=["10", "1.99", "15", "12.99"],
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

    product1_quantity = 3
    product2_quantity = 1
    product3_quantity = 2
    product4_quantity = 2

    # Step 1 - Create fixed sale for the products
    product_ids = [product1_id, product2_id, product3_id]
    discount_value = 10
    sale_id = prepare_sale_for_products(
        e2e_staff_api_client,
        channel_id,
        product_ids,
        sale_discount_type="FIXED",
        sale_discount_value=discount_value,
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 2 - Get product and check if it is on promotion
    for product_id in product_ids:
        product = next(p for p in products_data if p["product_id"] == product_id)

        variant_id = product["variant_id"]
        variant_price = float(product["price"])

        product_data = get_product(e2e_staff_api_client, product_id, channel_slug)

        assert product_data["id"] == product_id
        assert product_data["pricing"]["onSale"] is True

        variant_data = product_data["variants"][0]
        assert variant_data["id"] == variant_id
        assert variant_data["pricing"]["onSale"] is True
        discount_amount = variant_data["pricing"]["discount"]["gross"]["amount"]
        expected_discount = min(variant_price, 10)
        assert discount_amount == expected_discount

    # Step 3 - Create checkout and verify the total lines are not below 0
    lines = [
        {"variantId": product1_variant_id, "quantity": product1_quantity},
        {"variantId": product2_variant_id, "quantity": product2_quantity},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]
    assert checkout_id is not None
    checkout_line1 = checkout_data["lines"][0]
    assert checkout_line1["unitPrice"]["gross"]["amount"] == 0
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product1_variant_price
    assert checkout_line1["totalPrice"]["gross"]["amount"] == 0

    checkout_line2 = checkout_data["lines"][1]
    assert checkout_line2["unitPrice"]["gross"]["amount"] == 0
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line2["totalPrice"]["gross"]["amount"] == 0

    assert checkout_data["subtotalPrice"]["gross"]["amount"] == 0
    assert checkout_data["totalPrice"]["gross"]["amount"] == 0

    # Step 4 - Add Lines
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
    line3_calculated_unit_price = product3_variant_price - discount_value
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_calculated_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product3_variant_price
    assert (
        checkout_line3["totalPrice"]["gross"]["amount"]
        == product3_quantity * line3_calculated_unit_price
    )

    checkout_line4 = checkout_data["lines"][3]
    assert checkout_line4["unitPrice"]["gross"]["amount"] == product4_variant_price
    assert checkout_line4["undiscountedUnitPrice"]["amount"] == product4_variant_price
    assert (
        checkout_line4["totalPrice"]["gross"]["amount"]
        == product4_quantity * product4_variant_price
    )

    calculated_subtotal = round(
        line3_calculated_unit_price * product3_quantity
        + product4_variant_price * product4_quantity,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 5 - Update lines
    product1_new_quantity = 5
    product2_new_quantity = 10
    lines = [
        {
            "variantId": product1_variant_id,
            "quantity": product1_new_quantity,
        },
        {
            "variantId": product2_variant_id,
            "quantity": product2_new_quantity,
        },
    ]
    checkout_data = checkout_lines_update(
        e2e_not_logged_api_client,
        checkout_id,
        lines,
    )
    checkout_data = checkout_data["checkout"]
    checkout_line1 = checkout_data["lines"][0]
    assert checkout_line1["unitPrice"]["gross"]["amount"] == 0
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product1_variant_price
    assert checkout_line1["totalPrice"]["gross"]["amount"] == 0

    checkout_line2 = checkout_data["lines"][1]
    assert checkout_line2["unitPrice"]["gross"]["amount"] == 0
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product2_variant_price
    assert checkout_line2["totalPrice"]["gross"]["amount"] == 0

    calculated_subtotal = round(
        line3_calculated_unit_price * product3_quantity
        + product4_variant_price * product4_quantity,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 6 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    calculated_total = calculated_subtotal + shipping_price
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == calculated_total

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
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["subtotal"]["gross"]["amount"] == calculated_subtotal
    assert len(order_data["lines"]) == 4

    order_line1 = order_data["lines"][0]
    order_line2 = order_data["lines"][1]
    order_line3 = order_data["lines"][2]
    order_line4 = order_data["lines"][3]

    assert order_line1["quantity"] == product1_new_quantity
    assert order_line1["unitPrice"]["gross"]["amount"] == 0
    assert order_line1["unitDiscount"]["amount"] == product1_variant_price
    assert order_line1["unitDiscountReason"] == f"Sale: {sale_id}"
    assert (
        order_line1["undiscountedUnitPrice"]["gross"]["amount"]
        == product1_variant_price
    )
    assert order_line1["totalPrice"]["gross"]["amount"] == 0

    assert order_line2["quantity"] == product2_new_quantity
    assert order_line2["unitPrice"]["gross"]["amount"] == 0
    assert order_line2["unitDiscount"]["amount"] == product2_variant_price
    assert order_line2["unitDiscountReason"] == f"Sale: {sale_id}"
    assert (
        order_line2["undiscountedUnitPrice"]["gross"]["amount"]
        == product2_variant_price
    )
    assert order_line2["totalPrice"]["gross"]["amount"] == 0

    assert order_line3["quantity"] == product3_quantity
    assert order_line3["unitPrice"]["gross"]["amount"] == line3_calculated_unit_price
    assert order_line3["unitDiscount"]["amount"] == discount_value
    assert order_line3["unitDiscountReason"] == f"Sale: {sale_id}"
    assert (
        order_line3["undiscountedUnitPrice"]["gross"]["amount"]
        == product3_variant_price
    )
    assert (
        order_line3["totalPrice"]["gross"]["amount"]
        == product3_quantity * line3_calculated_unit_price
    )

    assert order_line4["quantity"] == product4_quantity
    assert order_line4["unitPrice"]["gross"]["amount"] == product4_variant_price
    assert order_line4["unitDiscount"]["amount"] == 0
    assert order_line4["unitDiscountReason"] is None
    assert (
        order_line4["undiscountedUnitPrice"]["gross"]["amount"]
        == product4_variant_price
    )
    assert (
        order_line4["totalPrice"]["gross"]["amount"]
        == product4_quantity * product4_variant_price
    )

    received_subtotal_from_lines = round(
        order_line1["totalPrice"]["gross"]["amount"]
        + order_line2["totalPrice"]["gross"]["amount"]
        + order_line3["totalPrice"]["gross"]["amount"]
        + order_line4["totalPrice"]["gross"]["amount"],
        2,
    )

    assert order_data["subtotal"]["gross"]["amount"] == received_subtotal_from_lines
