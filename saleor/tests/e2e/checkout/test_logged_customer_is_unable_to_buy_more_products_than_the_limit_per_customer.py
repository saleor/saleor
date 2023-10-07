import pytest

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
from .utils import checkout_create, checkout_lines_update


def prepare_product_with_limit(e2e_staff_api_client):
    (
        warehouse_id,
        channel_id,
        channel_slug,
        _shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

    product_type_data = create_product_type(
        e2e_staff_api_client,
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
        quantity_limit_per_customer=3,
    )
    product_variant_id = product_variant_data["id"]
    product_variant_name = product_variant_data["name"]
    product_variant_quantity_limit_per_customer = product_variant_data[
        "quantityLimitPerCustomer"
    ]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        price=10,
    )

    return (
        product_variant_id,
        product_variant_name,
        product_variant_quantity_limit_per_customer,
        channel_slug,
    )


@pytest.mark.e2e
def test_checkout_with_product_quantity_exceeding_the_limit_per_customer_core_0110(
    e2e_staff_api_client,
    e2e_logged_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)
    (
        product_variant_id,
        product_variant_name,
        product_variant_quantity_limit_per_customer,
        channel_slug,
    ) = prepare_product_with_limit(
        e2e_staff_api_client,
    )

    # Step 1 - Create checkout.
    lines = [
        {"variantId": product_variant_id, "quantity": 2},
    ]
    checkout_data = checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
    )
    checkout_id = checkout_data["id"]

    # Step 2 - Update checkout lines so quantity exceeds allowed limit per customer

    updatedLines = [
        {"variantId": product_variant_id, "quantity": 4},
    ]
    data = checkout_lines_update(
        e2e_logged_api_client,
        checkout_id,
        updatedLines,
    )
    errors = data["errors"]

    assert errors[0]["code"] == "QUANTITY_GREATER_THAN_LIMIT"
    assert errors[0]["field"] == "quantity"
    error_message = (
        f"Cannot add more than {product_variant_quantity_limit_per_customer} "
        f"times this item: {product_variant_name}."
    )
    assert errors[0]["message"] == error_message
