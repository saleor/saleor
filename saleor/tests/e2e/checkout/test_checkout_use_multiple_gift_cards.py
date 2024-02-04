import pytest

from ..gift_cards.utils import bulk_create_gift_card
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    raw_checkout_dummy_payment_create,
)


def prepare_gift_cards(
    e2e_staff_api_client,
    cards_amount,
    balance_amount,
):
    gift_card = bulk_create_gift_card(
        e2e_staff_api_client, cards_amount, balance_amount, "USD", active=True
    )
    first_code = gift_card[0]["code"]
    second_code = gift_card[1]["code"]
    third_code = gift_card[2]["code"]

    gift_card_codes = [first_code, second_code, third_code]

    return (
        first_code,
        second_code,
        third_code,
        balance_amount,
        gift_card_codes,
    )


@pytest.mark.e2e
def test_use_multiple_gift_cards_in_checkout_core_1105(
    e2e_logged_api_client,
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
        variant_price=9.99,
    )
    product_variant_price = float(product_variant_price)
    (
        first_code,
        second_code,
        third_code,
        balance_amount,
        gift_card_codes,
    ) = prepare_gift_cards(e2e_staff_api_client, 3, 5)

    # Step 1 - Create checkout for product
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 4,
        },
    ]
    checkout_data = checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]
    assert checkout_data["isShippingRequired"] is True
    calculated_subtotal = product_variant_price * 4
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 2 Add first gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_logged_api_client,
        checkout_id,
        first_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    total_with__first_gift_card = calculated_subtotal - balance_amount
    assert total_gross_amount == total_with__first_gift_card
    assert checkout_data["giftCards"][0]["last4CodeChars"] == first_code[-4:]

    # Step 3 Add second gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_logged_api_client,
        checkout_id,
        second_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    total_with_both_gift_cards = total_with__first_gift_card - balance_amount
    assert total_gross_amount == total_with_both_gift_cards
    assert checkout_data["giftCards"][0]["last4CodeChars"] == first_code[-4:]
    assert checkout_data["giftCards"][1]["last4CodeChars"] == second_code[-4:]

    # Step 4 Add third gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_logged_api_client,
        checkout_id,
        third_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    total_with_all_gift_cards = total_with_both_gift_cards - balance_amount
    assert total_gross_amount == total_with_all_gift_cards
    assert checkout_data["giftCards"][0]["last4CodeChars"] == first_code[-4:]
    assert checkout_data["giftCards"][1]["last4CodeChars"] == second_code[-4:]
    assert checkout_data["giftCards"][2]["last4CodeChars"] == third_code[-4:]

    # Step 5 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert shipping_price == 10
    calculated_total = total_with_all_gift_cards + shipping_price
    assert total_gross_amount == calculated_total

    # Step 4 - Create payment for checkout.
    create_payment = raw_checkout_dummy_payment_create(
        e2e_logged_api_client,
        checkout_id,
        total_gross_amount,
        token="fully_charged",
    )
    assert create_payment["errors"] == []
    assert create_payment["checkout"]["id"] == checkout_id

    # Step 5 - Complete checkout and check total
    order_data = checkout_complete(
        e2e_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert len(order_data["giftCards"]) == 3

    for i in range(3):
        expected_last_4 = gift_card_codes[i][-4:]
        actual_codes = [
            gift_card["last4CodeChars"] for gift_card in order_data["giftCards"]
        ]
        assert any(expected_last_4 in code for code in actual_codes)
