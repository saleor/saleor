import pytest

from ....channel import MarkAsPaidStrategy
from ...e2e.utils import assign_permissions
from ..channel.utils import update_channel
from ..gift_cards.utils import create_gift_card
from ..product.utils.preparing_product import prepare_products
from ..shop.utils.preparing_shop import prepare_default_shop
from .utils import checkout_add_promo_code, checkout_create, get_checkout


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("mark_as_paid_strategy", "expected_total_balance_after_adding_gift_card"),
    [
        (MarkAsPaidStrategy.TRANSACTION_FLOW.upper(), -44.99),
        (MarkAsPaidStrategy.PAYMENT_FLOW.upper(), -34.99),
    ],
)
def test_checkout_total_balance_with_gift_card(
    e2e_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_gift_card,
    permission_manage_orders,
    mark_as_paid_strategy,
    expected_total_balance_after_adding_gift_card,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_gift_card,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    update_channel(
        e2e_staff_api_client,
        channel_id,
        input={"orderSettings": {"markAsPaidStrategy": mark_as_paid_strategy}},
    )

    products_data = prepare_products(
        e2e_staff_api_client, warehouse_id, channel_id, [24.99, 5]
    )
    product1_variant_id = products_data[0]["variant_id"]
    product1_variant_price = float(products_data[0]["price"])

    product2_variant_id = products_data[1]["variant_id"]
    product2_variant_price = float(products_data[1]["price"])

    product1_quantity = 1
    product2_quantity = 4

    gift_card = create_gift_card(e2e_staff_api_client, 10, "USD", active=True)
    gift_card_code = gift_card["code"]

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

    # Step 2 - Check checkout total balance
    checkout_data = get_checkout(e2e_logged_api_client, checkout_data["id"])
    total_balance_amount = checkout_data["totalBalance"]["amount"]
    assert total_balance_amount == -calculated_subtotal

    # Step 3 - Add gift card to checkout
    checkout_add_promo_code(
        e2e_logged_api_client,
        checkout_id,
        gift_card_code,
    )

    # Step 4 - Check checkout total balance
    checkout_data = get_checkout(e2e_logged_api_client, checkout_data["id"])
    total_balance_amount = checkout_data["totalBalance"]["amount"]
    assert total_balance_amount == expected_total_balance_after_adding_gift_card
