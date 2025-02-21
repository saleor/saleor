import pytest

from ..orders.utils import order_by_checkout_id_query
from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..transactions.utils import create_transaction
from ..utils import assign_permissions
from .utils import (
    checkout_create,
    checkout_delivery_method_update,
)


@pytest.mark.e2e
def test_automatically_complete_checkout_paid_by_transaction_create_authorization_flow_CORE_0127(
    e2e_app_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_payments,
    shop_permissions,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_payments,
    ]
    assign_permissions(e2e_app_api_client, permissions)

    shop_data, _tax_config = prepare_shop(
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
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    variant_price = 10

    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_app_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    assert shipping_method_id is not None

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

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None
    assert checkout_data["shippingMethod"] is None
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

    # Step 3 - Create transaction that authorize payment
    psp_reference = "PSP-test"
    transaction_data = create_transaction(
        e2e_app_api_client,
        checkout_id,
        transaction_name="transaction",
        psp_reference=psp_reference,
        available_actions=["CHARGE", "CANCEL"],
        amount_authorized=total_gross_amount,
    )
    transaction_id = transaction_data["id"]

    # Step 4 - verify if the order has been created
    order_data = order_by_checkout_id_query(e2e_app_api_client, checkout_id)

    assert order_data["chargeStatus"] == "NONE"
    assert order_data["authorizeStatus"] == "FULL"
    assert len(order_data["transactions"]) == 1
    assert order_data["transactions"][0]["id"] == transaction_id
    assert order_data["transactions"][0]["pspReference"] == psp_reference
    event_types = [event_data["type"] for event_data in order_data["events"]]
    assert "PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT" in event_types
