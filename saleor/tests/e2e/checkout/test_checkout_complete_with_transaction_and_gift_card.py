import pytest

from ..gift_cards.utils import create_gift_card
from ..orders.utils import order_query
from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..transactions.utils import create_transaction
from ..utils import assign_permissions
from .utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
)


@pytest.mark.e2e
def test_checkout_complete_with_transaction_and_gift_card(
    e2e_app_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_payments,
    permission_manage_gift_card,
    shop_permissions,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_payments,
        permission_manage_gift_card,
    ]
    assign_permissions(e2e_app_api_client, permissions)

    shop_data, _ = prepare_shop(
        e2e_app_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {
                    "allowUnpaidOrders": False,
                    "markAsPaidStrategy": "TRANSACTION_FLOW",
                },
            }
        ],
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    variant_price = 10

    (
        _,
        product_variant_id,
        _,
    ) = prepare_product(
        e2e_app_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    assert shipping_method_id is not None

    gift_card = create_gift_card(e2e_app_api_client, 100, "USD", active=True)
    gift_card_code = gift_card["code"]
    gift_card_id = gift_card["id"]

    # Step 1 - Create checkout
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]

    subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert subtotal_gross_amount == float(variant_price)

    # Step 2 - Update delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert shipping_price == 10
    assert total_gross_amount == subtotal_gross_amount + shipping_price
    assert checkout_data["chargeStatus"] == "NONE"
    assert checkout_data["authorizeStatus"] == "NONE"

    # Step 3 - Create transaction that partially authorize payment
    create_transaction(
        e2e_app_api_client,
        checkout_id,
        transaction_name="transaction",
        psp_reference="PSP-test",
        available_actions=["CHARGE", "CANCEL"],
        amount_authorized=subtotal_gross_amount,
    )

    # Step 4 - Add gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        gift_card_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == 0
    assert checkout_data["giftCards"][0]["id"] == gift_card_id
    assert checkout_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]

    # Step 5 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == 0


@pytest.mark.e2e
def test_checkout_complete_with_gift_card_and_transaction(
    e2e_app_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_payments,
    permission_manage_gift_card,
    shop_permissions,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_payments,
        permission_manage_gift_card,
    ]
    assign_permissions(e2e_app_api_client, permissions)

    shop_data, _ = prepare_shop(
        e2e_app_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {
                    "allowUnpaidOrders": False,
                    "markAsPaidStrategy": "TRANSACTION_FLOW",
                },
            }
        ],
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    variant_price = 10

    (
        _,
        product_variant_id,
        _,
    ) = prepare_product(
        e2e_app_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    assert shipping_method_id is not None

    gift_card = create_gift_card(e2e_app_api_client, 100, "USD", active=True)
    gift_card_code = gift_card["code"]
    gift_card_id = gift_card["id"]

    # Step 1 - Create checkout
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]

    subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert subtotal_gross_amount == float(variant_price)

    # Step 2 - Update delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert shipping_price == 10
    assert total_gross_amount == subtotal_gross_amount + shipping_price
    assert checkout_data["chargeStatus"] == "NONE"
    assert checkout_data["authorizeStatus"] == "NONE"

    # Step 3 - Add gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        gift_card_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == 0
    assert checkout_data["giftCards"][0]["id"] == gift_card_id
    assert checkout_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]

    # Step 4 - Create transaction that partially authorize payment
    create_transaction(
        e2e_app_api_client,
        checkout_id,
        transaction_name="transaction",
        psp_reference="PSP-test",
        available_actions=["CHARGE", "CANCEL"],
        amount_authorized=subtotal_gross_amount,
    )

    # Step 5 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == 0


@pytest.mark.e2e
def test_checkout_complete_with_only_gift_card(
    e2e_app_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_payments,
    permission_manage_gift_card,
    shop_permissions,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_payments,
        permission_manage_gift_card,
    ]
    assign_permissions(e2e_app_api_client, permissions)

    shop_data, _ = prepare_shop(
        e2e_app_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {
                    "allowUnpaidOrders": False,
                    "markAsPaidStrategy": "TRANSACTION_FLOW",
                },
            }
        ],
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    variant_price = 10

    (
        _,
        product_variant_id,
        _,
    ) = prepare_product(
        e2e_app_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    assert shipping_method_id is not None

    gift_card = create_gift_card(e2e_app_api_client, 100, "USD", active=True)
    gift_card_code = gift_card["code"]
    gift_card_id = gift_card["id"]

    # Step 1 - Create checkout
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]

    subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]
    assert subtotal_gross_amount == float(variant_price)

    # Step 2 - Update delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert shipping_price == 10
    assert total_gross_amount == subtotal_gross_amount + shipping_price
    assert checkout_data["chargeStatus"] == "NONE"
    assert checkout_data["authorizeStatus"] == "NONE"

    # Step 3 - Add gift card to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        gift_card_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == 0
    assert checkout_data["giftCards"][0]["id"] == gift_card_id
    assert checkout_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]

    # Step 4 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNCONFIRMED"
    assert order_data["total"]["gross"]["amount"] == 0

    # Step 5 - Check order status
    order_data = order_query(e2e_app_api_client, order_data["id"])
    assert order_data["status"] == "UNFULFILLED"
