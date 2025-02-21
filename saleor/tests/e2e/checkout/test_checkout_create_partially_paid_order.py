import pytest

from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..transactions.utils import create_transaction
from ..utils import assign_permissions
from .utils import (
    checkout_create,
    checkout_delivery_method_update,
    raw_checkout_complete,
)


@pytest.mark.e2e
def test_should_be_able_to_create_partially_paid_order_core_0112(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    e2e_app_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_payments,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_payments,
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
                "order_settings": {
                    "allowUnpaidOrders": True,
                },
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
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    app_permissions = [permission_manage_payments]
    assign_permissions(e2e_app_api_client, app_permissions)

    variant_price = 10

    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    assert shipping_method_id is not None
    # Step 1 - Create checkout.
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@saleor.io",
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None
    assert checkout_data["shippingMethod"] is None

    # Step 2 - Set shipping address and DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 3 - Create transaction for part of amount
    create_transaction(
        e2e_app_api_client,
        checkout_id,
        transaction_name="CreditCard",
        message="Charged",
        psp_reference="PSP-ref123",
        available_actions=["REFUND", "CANCEL"],
        amount_charged=1,
    )

    # Step 4 - Complete checkout and check created order
    data = raw_checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    order_data = data["order"]
    assert order_data["id"] is not None
    assert order_data["isShippingRequired"] is True
    assert order_data["paymentStatus"] == "PARTIALLY_CHARGED"
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["isPaid"] is False

    errors = data["errors"]
    assert errors == []
