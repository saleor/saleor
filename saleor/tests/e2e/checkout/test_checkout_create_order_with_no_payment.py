import pytest

from ..orders.utils.draft_order import draft_order_create
from .utils import (
    checkout_create,
    checkout_delivery_method_update,
    raw_checkout_complete,
)


@pytest.mark.e2e
def test_should_be_able_to_create_order_with_no_payment(
    e2e_staff_api_client,
    prepare_product,
):
    # Before
    product_variant_id, channel_id, channel_slug = prepare_product
    data = draft_order_create(
        e2e_staff_api_client,
        channel_id,
    )

    # Step 1 - Create checkout.
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_staff_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None
    assert checkout_data["shippingMethod"] is None
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]

    # Step 2 - Set shipping address and DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_staff_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 3 - Checkout complete results in the order creation
    data = raw_checkout_complete(e2e_staff_api_client, checkout_id)
    order_data = data["order"]
    print(order_data)
    # assert order_data["id"] is not None
    # assert order_data["isShippingRequired"] is True
    # assert order_data["paymentStatus"] == "NOT_CHARGED"
    # assert order_data["status"] == "UNCONFIRMED"
    # assert order_data["isPaid"] is False

    # errors = data["errors"]
    # assert errors == []
