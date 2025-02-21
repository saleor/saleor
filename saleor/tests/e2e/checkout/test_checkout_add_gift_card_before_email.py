import pytest

from ..gift_cards.utils import create_gift_card
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_update_email,
    raw_checkout_dummy_payment_create,
)


@pytest.mark.e2e
def test_add_gift_card_before_email_in_checkout_core_1104(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
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
    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=24.99,
    )
    product_variant_price = float(product_variant_price)
    gift_card = create_gift_card(e2e_staff_api_client, 10, "USD", active=True)
    gift_card_code = gift_card["code"]
    gift_card_id = gift_card["id"]
    gift_card_balance = gift_card["initialBalance"]["amount"]

    # Step 1 - Create checkout for product
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 3,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
    )
    checkout_id = checkout_data["id"]
    calculated_subtotal = product_variant_price * 3
    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal
    assert checkout_data["email"] is None

    # Step 2 Add gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        gift_card_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == calculated_subtotal - gift_card_balance
    assert checkout_data["giftCards"][0]["id"] == gift_card_id
    assert checkout_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]

    # Step 3 - Set email for checkout
    checkout_data = checkout_update_email(
        e2e_not_logged_api_client, checkout_id, "testEmail@saleor.io"
    )
    assert checkout_data["email"] == "testEmail@saleor.io"

    # Step 4 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert shipping_price == 10
    calculated_total = calculated_subtotal + shipping_price - gift_card_balance
    assert total_gross_amount == calculated_total

    # Step 5 - Create payment for checkout.
    create_payment = raw_checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
        token="fully_charged",
    )
    assert create_payment["errors"] == []
    assert create_payment["checkout"]["id"] == checkout_id

    # Step 6 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["giftCards"][0]["id"] == gift_card_id
    assert order_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]
