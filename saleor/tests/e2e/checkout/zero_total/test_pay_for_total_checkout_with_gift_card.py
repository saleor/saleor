import pytest

from ...channel.utils import update_channel
from ...gift_cards.utils import create_gift_card
from ...product.utils.preparing_product import prepare_products
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
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
def test_gift_card_total_payment_for_checkout_core_1101(
    e2e_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
    mark_as_paid_strategy,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_gift_card,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]
    update_channel(
        e2e_staff_api_client,
        channel_id,
        input={"orderSettings": {"markAsPaidStrategy": mark_as_paid_strategy}},
    )

    products_data = prepare_products(
        e2e_staff_api_client, warehouse_id, channel_id, [24.99, 5, 16]
    )
    product1_variant_id = products_data[0]["variant_id"]
    product1_variant_price = float(products_data[0]["price"])

    product2_variant_id = products_data[1]["variant_id"]
    product2_variant_price = float(products_data[1]["price"])

    product3_variant_id = products_data[2]["variant_id"]
    product3_variant_price = float(products_data[2]["price"])

    product1_quantity = 1
    product2_quantity = 4
    product3_quantity = 2

    gift_card = create_gift_card(e2e_staff_api_client, 100, "USD", active=True)
    gift_card_code = gift_card["code"]
    gift_card_id = gift_card["id"]

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
        e2e_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]
    calculated_subtotal = round(
        product1_variant_price * product1_quantity
        + product2_variant_price * product2_quantity,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 2 - Add more lines
    lines = [
        {
            "variantId": product3_variant_id,
            "quantity": product3_quantity,
        }
    ]
    checkout_data = checkout_lines_add(e2e_logged_api_client, checkout_id, lines)
    assert checkout_data["isShippingRequired"] is True
    calculated_subtotal = round(
        product1_variant_price * product1_quantity
        + product2_variant_price * product2_quantity
        + product3_variant_price * product3_quantity,
        2,
    )
    assert checkout_data["subtotalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 3 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert shipping_price == 10
    assert total_gross_amount == calculated_subtotal + shipping_price

    # Step 4 Add gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_logged_api_client,
        checkout_id,
        gift_card_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == 0
    assert checkout_data["giftCards"][0]["id"] == gift_card_id
    assert checkout_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]

    # Step 5 - Complete checkout.
    order_data = checkout_complete(
        e2e_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == 0
    assert order_data["giftCards"][0]["id"] == gift_card_id
    assert order_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]
