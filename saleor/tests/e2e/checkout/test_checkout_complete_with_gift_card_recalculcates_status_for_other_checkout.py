import pytest

from ..gift_cards.utils import create_gift_card
from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    get_checkout,
    raw_checkout_complete,
)


@pytest.mark.e2e
@pytest.mark.parametrize(
    "query_second_checkout_status_before_checkout_complete",
    [
        True,
        False,
    ],
)
def test_checkout_complete_with_gift_card_recalculcates_status_for_other_checkout(
    e2e_app_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_gift_card,
    shop_permissions,
    query_second_checkout_status_before_checkout_complete,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
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

    gift_card = create_gift_card(e2e_app_api_client, 20, "USD", active=True)
    gift_card_code = gift_card["code"]
    gift_card_id = gift_card["id"]

    # Step 1 - Create first checkout
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    first_checkout_id = checkout_data["id"]

    # Step 2 - Update delivery method for first checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        first_checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 3 - Add gift card to first checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        first_checkout_id,
        gift_card_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == 0
    assert checkout_data["giftCards"][0]["id"] == gift_card_id
    assert checkout_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]

    # Step 4 - Check first checkout status
    checkout_data = get_checkout(e2e_not_logged_api_client, first_checkout_id)
    assert checkout_data["authorizeStatus"] == "FULL"
    assert checkout_data["chargeStatus"] == "FULL"

    # Step 5 - Create second checkout
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    second_checkout_id = checkout_data["id"]

    # Step 6 - Update delivery method for second checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        second_checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 7 - Add gift card to second checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        second_checkout_id,
        gift_card_code,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == 0
    assert checkout_data["giftCards"][0]["id"] == gift_card_id
    assert checkout_data["giftCards"][0]["last4CodeChars"] == gift_card_code[-4:]

    # Step 8 - Check second checkout status
    checkout_data = get_checkout(e2e_not_logged_api_client, second_checkout_id)
    assert checkout_data["authorizeStatus"] == "FULL"
    assert checkout_data["chargeStatus"] == "FULL"

    # Step 9 - Complete first checkout
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        first_checkout_id,
    )
    assert order_data["id"] is not None

    # # Step 10 - Check second checkout status once again
    if query_second_checkout_status_before_checkout_complete:
        checkout_data = get_checkout(e2e_not_logged_api_client, second_checkout_id)
        assert checkout_data["authorizeStatus"] == "NONE"
        assert checkout_data["chargeStatus"] == "NONE"

    # Step 11 - Attempt to complete second checkout
    response = raw_checkout_complete(
        e2e_not_logged_api_client,
        second_checkout_id,
    )
    errors = response["errors"]
    assert len(errors) == 1
    assert errors[0] == {
        "code": "CHECKOUT_NOT_FULLY_PAID",
        "field": None,
        "message": "Provided payment methods can not cover the checkout's total amount",
    }
