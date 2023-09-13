import pytest

from ..product.utils import (
    create_category,
    create_digital_content,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions
from .utils import (
    checkout_billing_address_update,
    checkout_complete,
    checkout_create,
    checkout_dummy_payment_create,
)


def prepare_product(
    e2e_staff_api_client,
):
    (
        warehouse_id,
        channel_id,
        channel_slug,
        _shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

    product_type_data = create_product_type(
        e2e_staff_api_client,
        is_shipping_required=False,
        is_digital=True,
    )
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

    create_product_variant_channel_listing(
        e2e_staff_api_client, product_variant_id, channel_id, price=10
    )

    create_digital_content(e2e_staff_api_client, product_variant_id)
    return product_variant_id, channel_slug


@pytest.mark.e2e
def test_process_checkout_with_digital_product_CORE_0101(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_channels,
    permission_manage_products,
    permission_manage_shipping,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        permission_manage_channels,
        permission_manage_products,
        permission_manage_shipping,
    ]
    assign_permissions(e2e_staff_api_client, permissions)
    product_variant_id, channel_slug = prepare_product(
        e2e_staff_api_client,
    )

    # Step 1  - Create checkout.
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
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert checkout_data["isShippingRequired"] is False

    # Step 2 - Set billing address for checkout.
    checkout_billing_address_update(
        e2e_not_logged_api_client,
        checkout_id,
    )

    # Step 3  - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 4 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["isShippingRequired"] is False
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
