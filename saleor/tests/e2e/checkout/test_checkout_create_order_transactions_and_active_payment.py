import pytest

from ....payment.error_codes import PaymentErrorCode
from ..apps.utils import add_app
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..transactions.utils import transaction_initialize
from ..utils import assign_permissions
from .utils import (
    checkout_create,
    checkout_delivery_method_update,
)
from .utils.checkout_payment_create import raw_checkout_dummy_payment_create


@pytest.mark.e2e
def test_complete_checkout_with_transaction_and_active_payment_CORE_1601(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_apps,
    permission_manage_checkouts,
    permission_manage_orders,
    monkeypatch,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_apps,
        permission_manage_checkouts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    # create webhook app
    identifier = "webhook.app.identifier"
    app_input = {
        "name": "external_shipping",
        "identifier": identifier,
        "permissions": [
            "MANAGE_SHIPPING",
            "MANAGE_CHECKOUTS",
            "MANAGE_ORDERS",
            "MANAGE_PRODUCTS",
            "MANAGE_CHANNELS",
        ],
    }
    app_data = add_app(e2e_staff_api_client, app_input)
    app_identifier = app_data["app"]["identifier"]

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    variant_price = 10

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

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
        email="testEmail@example.com",
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
    # Step 2 - Set DeliveryMethod for checkout.
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 3 - Initialize transaction
    transaction_initialize(
        monkeypatch,
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
        app_identifier,
    )

    # Step 4 - Create payment for checkout
    checkout_payment_create_response = raw_checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
        token="fully_charged",
    )

    errors = checkout_payment_create_response["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] is None
    assert errors[0]["code"] == PaymentErrorCode.CHECKOUT_HAS_TRANSACTION.name
