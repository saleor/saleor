import pytest

from ....graphql.order.enums import OrderChargeStatusEnum
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
                    "automaticallyCompleteFullyPaidCheckouts": True,
                },
            }
        ],
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
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

    # Step 3 - create checkout
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        api_client,
        lines,
        channel_slug,
        email="jon.doe@saleor.io",
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
