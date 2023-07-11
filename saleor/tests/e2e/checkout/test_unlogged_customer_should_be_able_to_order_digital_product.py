import pytest

from ..channel.utils import create_channel
from ..product.utils import (
    create_category,
    create_digital_content,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
from ..shipping_zone.utils import create_shipping_zone
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse
from .utils import (
    checkout_billing_address_update,
    checkout_complete,
    checkout_create,
    checkout_dummy_payment_create,
)


def prepare_product(
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_channels,
    permission_manage_products,
    permission_manage_shipping,
    channel_slug,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]

    warehouse_ids = [warehouse_id]
    channel_data = create_channel(
        e2e_staff_api_client, slug=channel_slug, warehouse_ids=warehouse_ids
    )
    channel_id = channel_data["id"]

    channel_ids = [channel_id]
    create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=warehouse_ids,
        channel_ids=channel_ids,
    )

    product_type_data = create_product_type(
        e2e_staff_api_client,
        is_shipping_required=False,
        is_digital=True,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    product_data = create_product(e2e_staff_api_client, product_type_id, category_id)
    product_id = product_data["id"]

    create_product_channel_listing(e2e_staff_api_client, product_id, channel_id)

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
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
    )

    create_digital_content(e2e_staff_api_client, product_variant_id)
    return product_variant_id


@pytest.mark.e2e
def test_process_checkout_with_digital_product(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_channels,
    permission_manage_products,
    permission_manage_shipping,
    media_root,
):
    # Before
    channel_slug = "test-channel"
    product_variant_id = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        channel_slug,
    )

    # Step 1  - Create checkout.
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
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert checkout_data["isShippingRequired"] is False

    # Step 2 - Set billing address for checkout.
    checkout_billing_address_update(e2e_not_logged_api_client, checkout_id)

    # Step 3  - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client, checkout_id, total_gross_amount
    )

    # Step 4 - Complete checkout.
    order_data = checkout_complete(e2e_not_logged_api_client, checkout_id)
    assert order_data["isShippingRequired"] is False
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
