import pytest

from ..product.utils import (
    create_category,
    create_product,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
    raw_create_product_channel_listing,
)
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import raw_checkout_create


def prepare_unavailable_product(
    e2e_staff_api_client,
):
    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]

    product_type_data = create_product_type(
        e2e_staff_api_client,
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

    product_channel_listing = raw_create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        channel_id,
        is_available_for_purchase=False,
        available_for_purchase_datetime=None,
    )

    channel_listing_data = product_channel_listing["product"]["channelListings"][0]
    assert channel_listing_data["isAvailableForPurchase"] is False
    assert channel_listing_data["availableForPurchaseAt"] is None

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=stocks,
    )
    variant_id = variant_data["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        variant_id,
        channel_id,
        price=10,
    )

    return variant_id, channel_slug


@pytest.mark.e2e
def test_should_not_be_able_to_buy_unavailable_product_core_0108(
    e2e_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
    ]

    assign_permissions(e2e_staff_api_client, permissions)
    (
        variant_id,
        channel_slug,
    ) = prepare_unavailable_product(
        e2e_staff_api_client,
    )

    # Step 1 - Create checkout with non available for purchase product
    lines = [
        {
            "variantId": variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = raw_checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
    )

    errors = checkout_data["errors"]
    assert errors[0]["code"] == "PRODUCT_UNAVAILABLE_FOR_PURCHASE"
    assert errors[0]["field"] == "lines"
    assert (
        errors[0]["message"]
        == "Cannot add lines for unavailable for purchase variants."
    )
