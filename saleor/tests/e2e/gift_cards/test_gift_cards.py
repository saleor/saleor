import pytest

from ....graphql.order.enums import OrderChargeStatusEnum
from ....tests import race_condition
from ...e2e.utils import assign_permissions
from ..checkout.utils.checkout_add_promo_code import checkout_add_promo_code
from ..checkout.utils.checkout_complete import checkout_complete
from ..checkout.utils.checkout_create import checkout_create
from ..orders.utils.order_query import order_query
from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..transactions.utils.transaction_initialize import (
    transaction_initialize_for_gift_card_payment_gateway,
)
from .utils.gift_card_create import create_gift_card
from .utils.gift_card_query import get_gift_card


def _prepare_shop(staff_api_client):
    shop_data, _ = prepare_shop(
        staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {
                    "allowUnpaidOrders": False,
                    "automaticallyConfirmAllNewOrders": True,
                },
                "checkout_settings": {
                    "automaticallyCompleteFullyPaidCheckouts": False,
                },
            }
        ],
    )

    return shop_data


def _prepare_product(staff_api_client, shop_data):
    channel_id = shop_data[0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]

    variant_price = 10

    (
        _,
        product_variant_id,
        _,
    ) = prepare_product(
        staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
        is_shipping_required=False,
    )

    return product_variant_id, variant_price


def _prepare_checkout(api_client, lines, channel_slug):
    return checkout_create(
        api_client,
        lines,
        channel_slug,
        email="jon.doe@saleor.io",
    )


@pytest.mark.e2e
def test_gift_card_added_via_add_promo_code_and_transaction_does_not_use_the_same_funds_twice(
    api_client,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
    permission_manage_orders,
    shop_permissions,
):
    permissions = [
        permission_manage_product_types_and_attributes,
        permission_manage_gift_card,
        permission_manage_orders,
        *shop_permissions,
    ]

    assign_permissions(staff_api_client, permissions)

    # Step 1 - create gift card
    gift_card_initial_balance = 100
    gift_card_data = create_gift_card(staff_api_client, gift_card_initial_balance)

    # Step 2 - prepare channel and product
    shop_data = _prepare_shop(staff_api_client)
    channel_slug = shop_data[0]["slug"]
    product_variant_id, variant_price = _prepare_product(staff_api_client, shop_data)

    # Step 3 - create checkout
    checkout_data = _prepare_checkout(
        api_client,
        [
            {
                "variantId": product_variant_id,
                "quantity": 1,
            },
        ],
        channel_slug,
    )

    # Step 4 - add gift card to checkout with addPromoCode
    checkout_add_promo_code(api_client, checkout_data["id"], gift_card_data["code"])

    # Step 5 - add gift card to checkout via transaction
    transaction_initialize_for_gift_card_payment_gateway(
        api_client,
        checkout_data["id"],
        gift_card_data["code"],
        variant_price,
    )

    # Step 6 - complete checkout
    order_data = checkout_complete(api_client, checkout_data["id"])

    # Step 7 - check gift card funds
    gift_card_data = get_gift_card(staff_api_client, gift_card_data["id"])

    # Two times variant price because:
    # - gift card attached to checkout with checkoutAddPromoCode
    # - gift card attached to checkout with transaction
    assert gift_card_data["currentBalance"]["amount"] == gift_card_initial_balance - (
        2 * variant_price
    )

    # Step 8 - check order payment status and gift card transaction
    order_data = order_query(staff_api_client, order_data["id"])
    assert order_data["chargeStatus"] == OrderChargeStatusEnum.OVERCHARGED.name
    assert len(order_data["transactions"]) == 1
    assert order_data["transactions"][0]["authorizedAmount"]["amount"] == 0
    assert order_data["transactions"][0]["chargedAmount"]["amount"] == 10


@pytest.mark.e2e
def test_gift_card_detach_gift_card_from_checkout_as_gift_card_transactions_are_about_to_get_charged(
    api_client,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
    permission_manage_orders,
    shop_permissions,
):
    permissions = [
        permission_manage_product_types_and_attributes,
        permission_manage_gift_card,
        permission_manage_orders,
        *shop_permissions,
    ]

    assign_permissions(staff_api_client, permissions)

    # Step 1 - create gift card
    gift_card_initial_balance = 100
    gift_card_data = create_gift_card(staff_api_client, gift_card_initial_balance)

    # Step 2 - prepare channel and product
    shop_data = _prepare_shop(staff_api_client)
    channel_slug = shop_data[0]["slug"]
    product_variant_id, variant_price = _prepare_product(staff_api_client, shop_data)

    # Step 3 - create checkout
    checkout_data = _prepare_checkout(
        api_client,
        [
            {
                "variantId": product_variant_id,
                "quantity": 1,
            },
        ],
        channel_slug,
    )

    # Step 4 - add gift card to checkout via transaction
    transaction_initialize_for_gift_card_payment_gateway(
        api_client,
        checkout_data["id"],
        gift_card_data["code"],
        variant_price,
    )

    # Step 5 - complete checkout
    def attach_gift_card_to_another_checkout(*args, **kwargs):
        another_checkout_data = _prepare_checkout(
            api_client,
            [],
            channel_slug,
        )
        transaction_initialize_for_gift_card_payment_gateway(
            api_client,
            another_checkout_data["id"],
            gift_card_data["code"],
            1,
        )

    with race_condition.RunBefore(
        # At this point gift card will not get detached because when
        # charge_gift_card_transactions is executed the transaction is no longer
        # attached to a checkout (but to an order)
        "saleor.giftcard.gateway.charge_gift_card_transactions",
        attach_gift_card_to_another_checkout,
    ):
        order_data = checkout_complete(api_client, checkout_data["id"])

    # Step 6 - check gift card funds
    gift_card_data = get_gift_card(staff_api_client, gift_card_data["id"])

    assert (
        gift_card_data["currentBalance"]["amount"]
        == gift_card_initial_balance - variant_price
    )

    # Step 7 - check order payment status and gift card transaction
    order_data = order_query(staff_api_client, order_data["id"])
    assert order_data["chargeStatus"] == OrderChargeStatusEnum.FULL.name
    assert len(order_data["transactions"]) == 1
    assert order_data["transactions"][0]["authorizedAmount"]["amount"] == 0
    assert order_data["transactions"][0]["chargedAmount"]["amount"] == variant_price


@pytest.mark.e2e
def test_gift_card_detach_gift_card_from_checkout_as_checkout_gets_completed(
    api_client,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
    permission_manage_orders,
    shop_permissions,
):
    permissions = [
        permission_manage_product_types_and_attributes,
        permission_manage_gift_card,
        permission_manage_orders,
        *shop_permissions,
    ]

    assign_permissions(staff_api_client, permissions)

    # Step 1 - create gift card
    gift_card_initial_balance = 100
    gift_card_data = create_gift_card(staff_api_client, gift_card_initial_balance)

    # Step 2 - prepare channel and product
    shop_data = _prepare_shop(staff_api_client)
    channel_slug = shop_data[0]["slug"]
    product_variant_id, variant_price = _prepare_product(staff_api_client, shop_data)

    # Step 3 - create checkout
    checkout_data = _prepare_checkout(
        api_client,
        [
            {
                "variantId": product_variant_id,
                "quantity": 1,
            },
        ],
        channel_slug,
    )

    # Step 4 - add gift card to checkout via transaction
    transaction_initialize_for_gift_card_payment_gateway(
        api_client,
        checkout_data["id"],
        gift_card_data["code"],
        variant_price,
    )

    # Step 5 - complete checkout
    def attach_gift_card_to_another_checkout(*args, **kwargs):
        another_checkout_data = _prepare_checkout(
            api_client,
            [],
            channel_slug,
        )
        transaction_initialize_for_gift_card_payment_gateway(
            api_client,
            another_checkout_data["id"],
            gift_card_data["code"],
            1,
        )

    with race_condition.RunBefore(
        # Complete checkout logic can get started because checkout's authorization
        # status is set to full at that time. Just before order gets created and transactions are charged the
        # gift card is detached from the checkout.
        "saleor.checkout.complete_checkout.create_order_from_checkout",
        attach_gift_card_to_another_checkout,
    ):
        order_data = checkout_complete(api_client, checkout_data["id"])

    # Step 6 - check gift card funds
    gift_card_data = get_gift_card(staff_api_client, gift_card_data["id"])

    assert gift_card_data["currentBalance"]["amount"] == gift_card_initial_balance

    # Step 7 - check order payment status and gift card transaction
    order_data = order_query(staff_api_client, order_data["id"])
    assert order_data["chargeStatus"] == OrderChargeStatusEnum.NONE.name
    assert len(order_data["transactions"]) == 1
    assert order_data["transactions"][0]["authorizedAmount"]["amount"] == 0
    assert order_data["transactions"][0]["chargedAmount"]["amount"] == 0


@pytest.mark.e2e
def test_gift_card_simultaneous_complete_checkout_of_two_checkouts_using_gift_card_differently(
    api_client,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
    permission_manage_orders,
    shop_permissions,
):
    permissions = [
        permission_manage_product_types_and_attributes,
        permission_manage_gift_card,
        permission_manage_orders,
        *shop_permissions,
    ]

    assign_permissions(staff_api_client, permissions)

    # Step 1 - create gift card
    gift_card_initial_balance = 100
    gift_card_data = create_gift_card(staff_api_client, gift_card_initial_balance)

    # Step 2 - prepare channel and product
    shop_data = _prepare_shop(staff_api_client)
    channel_slug = shop_data[0]["slug"]
    product_variant_id, variant_price = _prepare_product(staff_api_client, shop_data)

    # Step 3 - create checkout
    checkout_data = _prepare_checkout(
        api_client,
        [
            {
                "variantId": product_variant_id,
                "quantity": 1,
            },
        ],
        channel_slug,
    )

    # Step 4 - add gift card to checkout with addPromoCode
    checkout_add_promo_code(api_client, checkout_data["id"], gift_card_data["code"])

    # Step 5 - create another checkout
    another_checkout_data = _prepare_checkout(
        api_client,
        [
            {
                "variantId": product_variant_id,
                "quantity": 1,
            },
        ],
        channel_slug,
    )

    # Step 6 - add gift card to another checkout via transaction
    transaction_initialize_for_gift_card_payment_gateway(
        api_client,
        another_checkout_data["id"],
        gift_card_data["code"],
        variant_price,
    )

    # Step 6 - complete checkout
    order_data = None

    def do_complete_checkout(*args, **kwargs):
        nonlocal order_data
        order_data = checkout_complete(api_client, checkout_data["id"])

    with race_condition.RunBefore(
        "saleor.giftcard.gateway.charge_gift_card_transactions",
        do_complete_checkout,
    ):
        another_order_data = checkout_complete(api_client, another_checkout_data["id"])

    # Step 6 - check gift card funds
    gift_card_data = get_gift_card(staff_api_client, gift_card_data["id"])

    assert gift_card_data["currentBalance"]["amount"] == gift_card_initial_balance - (
        2 * variant_price
    )

    # Step 7 - check order payment status and gift card transaction
    order_data = order_query(staff_api_client, order_data["id"])
    assert order_data["chargeStatus"] == OrderChargeStatusEnum.FULL.name
    assert len(order_data["transactions"]) == 0

    another_order_data = order_query(staff_api_client, another_order_data["id"])
    assert another_order_data["chargeStatus"] == OrderChargeStatusEnum.FULL.name
    assert len(another_order_data["transactions"]) == 1
    assert another_order_data["transactions"][0]["authorizedAmount"]["amount"] == 0
    assert (
        another_order_data["transactions"][0]["chargedAmount"]["amount"]
        == variant_price
    )
