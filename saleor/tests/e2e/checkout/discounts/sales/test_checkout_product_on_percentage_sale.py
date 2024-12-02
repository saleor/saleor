import pytest

from ......product.tasks import recalculate_discounted_price_for_products_task
from ....product.utils.preparing_product import prepare_product
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
    checkout_lines_delete,
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

    return sale_id, sale_discount_value


def prepare_products(
    e2e_staff_api_client,
    warehouse_id,
    channel_id,
    number_of_products,
    prices,
):
    if len(prices) < number_of_products:
        raise ValueError("Not enough prices provided for the number of products.")

    products_data = []

    for i in range(number_of_products):
        variant_price = prices[i]
        product_id, variant_id, price = prepare_product(
            e2e_staff_api_client,
            warehouse_id,
            channel_id,
            variant_price,
            product_type_slug=f"test-{i}",
        )
        product_data = {
            "product_id": product_id,
            "variant_id": variant_id,
            "price": price,
        }
        products_data.append(product_data)

    return products_data


@pytest.mark.e2e
def test_checkout_products_on_percentage_sale_core_1004(
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

    products_data = prepare_products(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        4,
        ["13.33", "15", "9.99", "20.5"],
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
        sale_discount_value=3,
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 1 - checkoutCreate for product on sale
    lines = [
        {
            "variantId": product1_variant_id,
            "quantity": 2,
        },
        {
            "variantId": product2_variant_id,
            "quantity": 4,
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
    checkout_line1 = checkout_data["lines"][0]
    checkout_line2 = checkout_data["lines"][1]

    assert checkout_line1["variant"]["id"] == product1_variant_id
    assert checkout_line1["quantity"] == 2
    line1_discount = round(product1_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product1_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == product1_variant_price

    assert checkout_line2["variant"]["id"] == product2_variant_id
    assert checkout_line2["quantity"] == 4
    line2_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = product2_variant_price - line2_discount
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == product2_variant_price

    assert (
        checkout_data["subtotalPrice"]["gross"]["amount"]
        == 2 * line1_unit_price + 4 * line2_unit_price
    )

    # Step 2 - Add Lines
    lines = [
        {
            "variantId": product3_variant_id,
            "quantity": 1,
        },
        {
            "variantId": product4_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_lines_add(
        e2e_not_logged_api_client,
        checkout_id,
        lines,
    )
    checkout_line3 = checkout_data["lines"][2]
    assert checkout_line3["variant"]["id"] == product3_variant_id
    assert checkout_line3["quantity"] == 1
    line3_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line3_unit_price = product3_variant_price - line3_discount
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == product3_variant_price

    checkout_line4 = checkout_data["lines"][3]
    assert checkout_line4["variant"]["id"] == product4_variant_id
    assert checkout_line4["quantity"] == 1
    line4_unit_price = product4_variant_price
    assert checkout_line4["unitPrice"]["gross"]["amount"] == line4_unit_price
    assert checkout_line4["undiscountedUnitPrice"]["amount"] == line4_unit_price
    assert (
        checkout_data["subtotalPrice"]["gross"]["amount"]
        == 2 * line1_unit_price
        + 4 * line2_unit_price
        + line3_unit_price
        + line4_unit_price
    )

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
    assert new_checkout_line1["quantity"] == 4
    line1_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product2_variant_price - line1_discount
    assert new_checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert new_checkout_line1["undiscountedUnitPrice"]["amount"] == float(
        product2_variant_price
    )

    assert new_checkout_line2["variant"]["id"] == product3_variant_id
    assert new_checkout_line2["quantity"] == 1
    line2_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = product3_variant_price - line2_discount
    assert new_checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert new_checkout_line2["undiscountedUnitPrice"]["amount"] == float(
        product3_variant_price
    )

    assert new_checkout_line3["variant"]["id"] == product4_variant_id
    assert new_checkout_line3["quantity"] == 1
    line3_unit_price = product4_variant_price
    assert new_checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert new_checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    assert (
        checkout_data["subtotalPrice"]["gross"]["amount"]
        == (4 * line1_unit_price) + line2_unit_price + line3_unit_price
    )

    # Step 4 - Update lines
    lines = [
        {
            "quantity": 3,
            "lineId": new_checkout_line1["id"],
        },
        {
            "quantity": 2,
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
    assert checkout_line1["quantity"] == 3
    line1_discount = round(product2_variant_price * sale_discount_value / 100, 2)
    line1_unit_price = product2_variant_price - line1_discount
    assert checkout_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert checkout_line1["undiscountedUnitPrice"]["amount"] == float(
        product2_variant_price
    )

    assert checkout_line2["variant"]["id"] == product3_variant_id
    assert checkout_line2["quantity"] == 2
    line2_discount = round(product3_variant_price * sale_discount_value / 100, 2)
    line2_unit_price = product3_variant_price - line2_discount
    assert checkout_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert checkout_line2["undiscountedUnitPrice"]["amount"] == float(
        product3_variant_price
    )

    assert checkout_line3["variant"]["id"] == product4_variant_id
    assert checkout_line3["quantity"] == 1
    line3_unit_price = product4_variant_price
    assert checkout_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert checkout_line3["undiscountedUnitPrice"]["amount"] == line3_unit_price
    calculated_subtotal = (
        (3 * line1_unit_price) + 2 * line2_unit_price + line3_unit_price
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 5 - Set DeliveryMethod for checkout.
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
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["subtotal"]["gross"]["amount"] == calculated_subtotal

    order_line1 = order_data["lines"][0]
    order_line2 = order_data["lines"][1]
    order_line3 = order_data["lines"][2]

    assert len(order_data["lines"]) == 3

    assert order_line1["quantity"] == 3
    assert order_line1["unitPrice"]["gross"]["amount"] == line1_unit_price
    assert order_line1["unitDiscount"]["amount"] == line1_discount
    assert order_line1["unitDiscountReason"] == f"Sale: {sale_id}"
    assert (
        order_line1["undiscountedUnitPrice"]["gross"]["amount"]
        == product2_variant_price
    )

    assert order_line2["quantity"] == 2
    assert order_line2["unitPrice"]["gross"]["amount"] == line2_unit_price
    assert order_line2["unitDiscount"]["amount"] == line2_discount
    assert order_line2["unitDiscountReason"] == f"Sale: {sale_id}"
    assert (
        order_line2["undiscountedUnitPrice"]["gross"]["amount"]
        == product3_variant_price
    )

    assert order_line3["quantity"] == 1
    assert order_line3["unitPrice"]["gross"]["amount"] == line3_unit_price
    assert order_line3["unitDiscount"]["amount"] == 0
    assert order_line3["unitDiscountReason"] is None
    assert (
        order_line3["undiscountedUnitPrice"]["gross"]["amount"]
        == product4_variant_price
    )

    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["subtotal"]["gross"]["amount"] == calculated_subtotal
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price
