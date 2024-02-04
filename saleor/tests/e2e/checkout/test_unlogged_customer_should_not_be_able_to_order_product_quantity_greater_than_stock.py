import pytest

from ..product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant_channel_listing,
    raw_create_product_variant,
)
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import raw_checkout_create


def prepare_product(
    e2e_staff_api_client,
):
    shop_data = prepare_default_shop(e2e_staff_api_client)

    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]

    product_type_data = create_product_type(
        e2e_staff_api_client,
        is_shipping_required=True,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(
        e2e_staff_api_client,
    )
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

    stock_quantity = 5

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": stock_quantity,
        }
    ]
    variant_data = raw_create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=stocks,
    )
    product_variant_id = variant_data["productVariant"]["id"]
    product_variant_name = variant_data["productVariant"]["name"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        price=10,
    )

    return (
        product_variant_id,
        product_variant_name,
        channel_slug,
        stock_quantity,
    )


@pytest.mark.e2e
def test_unlogged_customer_cannot_buy_product_in_quantity_grater_than_stock_core_0107(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        *shop_permissions,
    ]
    assign_permissions(e2e_staff_api_client, permissions)
    (
        product_variant_id,
        product_variant_name,
        channel_slug,
        stock_quantity,
    ) = prepare_product(
        e2e_staff_api_client,
    )
    # Step 1 - Create checkout with product quantity greater than the available stock
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": stock_quantity + 1,
        },
    ]
    checkout_data = raw_checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="jon.doe@saleor.io",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )

    errors = checkout_data["errors"]
    assert errors[0]["code"] == "INSUFFICIENT_STOCK"
    assert errors[0]["field"] == "quantity"
    assert (
        errors[0]["message"] == f"Could not add items {product_variant_name}. "
        f"Only {stock_quantity} remaining in stock."
    )
