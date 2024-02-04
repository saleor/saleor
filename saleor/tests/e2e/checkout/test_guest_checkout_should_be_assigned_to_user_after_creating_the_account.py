import pytest

from ..account.utils import account_register
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..users.utils import customer_update, get_user
from ..utils import assign_permissions
from .utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


@pytest.mark.e2e
def test_guest_checkout_should_be_assigned_to_user_after_creating_the_account_CORE_1518(
    e2e_staff_api_client,
    app_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_users,
    permission_manage_payments,
    shop_permissions,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_users,
        permission_manage_payments,
    ]
    assign_permissions(
        app_api_client,
        [
            permission_manage_checkouts,
            permission_manage_orders,
            permission_manage_payments,
        ],
    )
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
                "order_settings": {},
            }
        ],
        shop_settings={
            "enableAccountConfirmationByEmail": False,
        },
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
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    # Step 1 - Create checkout
    email = "test@saleor.io"
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        app_api_client,
        lines,
        channel_slug,
        email,
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None

    # Step 2 - Set DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        app_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 3 - Create payment for checkout
    checkout_dummy_payment_create(
        app_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 4 - Complete checkout
    order_data = checkout_complete(
        app_api_client,
        checkout_id,
    )
    order_id = order_data["id"]
    assert order_data["isShippingRequired"] is True
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 5 - Register new account
    password = "Test1234!"
    redirect_url = "https://www.example.com"
    user_account = account_register(
        e2e_not_logged_api_client,
        email,
        password,
        channel_slug,
        redirect_url,
    )
    user_id = user_account["user"]["id"]
    assert user_account["user"]["isActive"] is True

    # Step 6 - Confirm new account
    input_data = {"isConfirmed": True}
    customer_update(e2e_staff_api_client, user_id, input_data)

    # Step 7 - Check the order is assigned to the customer's account
    data = get_user(e2e_staff_api_client, user_id)
    assert data["id"] == user_id
    assert data["orders"]["edges"][0]["node"]["id"] == order_id
