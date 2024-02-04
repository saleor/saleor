import pytest

from ..account.utils import get_own_data
from ..gift_cards.utils import get_gift_cards
from ..orders.utils import order_query
from ..product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions
from .utils import (
    checkout_complete,
    checkout_create,
    checkout_dummy_payment_create,
)


def prepare_product_gift_card(
    e2e_staff_api_client,
    warehouse_id,
    channel_id,
):
    product_type_data = create_product_type(
        e2e_staff_api_client,
        product_type_name="Gift card product type",
        slug="gc-type",
        is_shipping_required=False,
        is_digital=True,
        kind="GIFT_CARD",
    )
    assert product_type_data["kind"] == "GIFT_CARD"
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id = product_data["id"]

    create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        channel_id,
    )

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    product_variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=stocks,
    )
    product_variant_id = product_variant_data["id"]
    product_variant_price = 25

    create_product_variant_channel_listing(
        e2e_staff_api_client, product_variant_id, channel_id, product_variant_price
    )

    return product_variant_id, product_variant_price, product_id


@pytest.mark.e2e
def test_buy_gift_card_in_the_checkout_CORE_1102(
    e2e_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
    permission_manage_orders,
    permission_manage_plugins,
    shop_permissions,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        *shop_permissions,
        permission_manage_gift_card,
        permission_manage_orders,
        permission_manage_plugins,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {"automaticallyFulfillNonShippableGiftCard": True},
            }
        ],
        shop_settings={
            "fulfillmentAutoApprove": True,
            "fulfillmentAllowUnpaid": True,
        },
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]

    product_variant_id, _product_variant_price, _product_id = prepare_product_gift_card(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
    )

    # Step 1  - Create checkout.
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
    )
    checkout_id = checkout_data["id"]
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert checkout_data["isShippingRequired"] is False

    # Step 2  - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 3 - Complete checkout.
    order_data = checkout_complete(
        e2e_logged_api_client,
        checkout_id,
    )
    assert order_data["isShippingRequired"] is False
    assert order_data["total"]["gross"]["amount"] == total_gross_amount

    # extra query because order need a time to change status
    me = get_own_data(e2e_logged_api_client)
    assert len(me["orders"]["edges"]) == 1

    # 4 Get Order
    order = order_query(e2e_staff_api_client, order_data["id"])
    assert order["status"] == "FULFILLED"

    # Step 5 - Verify created gift card
    gift_cards_data = get_gift_cards(e2e_staff_api_client, 10)
    assert len(gift_cards_data) == 1
