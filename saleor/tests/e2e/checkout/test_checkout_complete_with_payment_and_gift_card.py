import pytest

from ..gift_cards.utils.gift_card_create import create_gift_card
from ..gift_cards.utils.gift_card_query import gift_card_query
from ..orders.utils.order_query import order_query
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)

@pytest.mark.e2e
@pytest.mark.parametrize(("create_transactions_for_gift_cards"), [True, False])
def test_checkout_complete_does_not_use_create_transactions_for_gift_cards_flow_when_payment_is_mixed_with_gift_card(
    e2e_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
    permission_manage_orders,
    create_transactions_for_gift_cards,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_gift_card,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(
        e2e_staff_api_client,
        channel_checkout_settings={
            "createTransactionsForGiftCards": create_transactions_for_gift_cards
        },
    )

    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        _,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=9.99,
    )
    product_variant_price = float(product_variant_price)

    gift_card = create_gift_card(e2e_staff_api_client, 5, "USD", active=True)
    gift_card_id = gift_card["id"]
    gift_card_code = gift_card["code"]
    gift_card_initial_balance = gift_card["initialBalance"]["amount"]

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
    )
    checkout_id = checkout_data["id"]
    assert checkout_data["isShippingRequired"] is True
    calculated_subtotal = product_variant_price * 4
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal

    # Step 2 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    shipping_price = 10
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["shippingPrice"]["gross"]["amount"] == shipping_price
    assert (
        checkout_data["totalPrice"]["gross"]["amount"]
        == calculated_subtotal + shipping_price
    )

    # Step 3 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_logged_api_client,
        checkout_id,
        calculated_subtotal + shipping_price,
    )

    # Step 4 - Add gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_logged_api_client,
        checkout_id,
        gift_card_code,
    )
    assert checkout_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]

    # Step 5 - Complete checkout
    order_data = checkout_complete(
        e2e_logged_api_client,
        checkout_id,
    )
    assert order_data["id"] is not None
    assert (
        order_data["total"]["gross"]["amount"]
        == calculated_subtotal + shipping_price - gift_card_initial_balance
    ), "Order total should have been reduced by gift card"

    # Step 6 - Check for transactions
    order_data = order_query(
        e2e_staff_api_client,
        order_data["id"],
    )
    assert len(order_data["transactions"]) == 0, (
        "No TransactionItem should have been created"
    )

    # Step 7 - Check whether funds are consumed from gift card
    gift_card_data = gift_card_query(e2e_staff_api_client, gift_card_id)
    assert gift_card_data["initialBalance"]["amount"] == gift_card_initial_balance
    assert gift_card_data["currentBalance"]["amount"] == 0, (
        "Entire amount should have been used by the Order"
    )
