import pytest

from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import checkout_create, checkout_delivery_method_update


@pytest.mark.e2e
def test_checkout_should_be_able_to_remove_shipping_method_CORE_0115(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
    permission_manage_orders,
    permission_manage_checkouts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

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
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]
    assert checkout_data["shippingMethods"] != []
    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == variant_price

    # Step 2 - Set DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    subtotal_price = checkout_data["subtotalPrice"]["gross"]["amount"]
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    assert subtotal_price == float(variant_price)
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert total_gross_amount == float(subtotal_price + shipping_price)

    # Step 3 - Remove shipping method from the checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    shipping_price = checkout_data["shippingPrice"]["gross"]["amount"]
    assert shipping_price == 0
    assert total_gross_amount == float(variant_price)
    assert checkout_data["deliveryMethod"] is None
