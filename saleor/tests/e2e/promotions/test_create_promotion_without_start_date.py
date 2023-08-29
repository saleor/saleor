from datetime import date

import pytest

from ..channel.utils import create_channel
from ..product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
    get_product,
)
from ..promotions.utils import create_promotion, create_promotion_rule
from ..utils import assign_permissions


def prepare_product(
    e2e_staff_api_client,
    channel_slug,
):
    channel_data = create_channel(
        e2e_staff_api_client,
        slug=channel_slug,
    )
    channel_id = channel_data["id"]

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
    create_product_channel_listing(e2e_staff_api_client, product_id, channel_id)

    variant_data = create_product_variant(e2e_staff_api_client, product_id)
    product_variant_id = variant_data["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
    )

    return product_id, product_variant_id, channel_id


@pytest.mark.e2e
def test_create_promotion_without_start_date(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before
    channel_slug = "test-channel"
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        product_id,
        product_variant_id,
        channel_id,
    ) = prepare_product(
        e2e_staff_api_client,
        channel_slug,
    )

    channel_slug = "test-channel"
    promotion_name = "Promotion Fixed"
    discount_value = 10
    discount_type = "PERCENTAGE"
    promotion_rule_name = "rule for product"
    current_date = date.today().isoformat()

    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, start_date=None
    )
    promotion_id = promotion_data["id"]
    promotion_start_date = promotion_data["startDate"].split("T")[0]

    assert promotion_id is not None
    assert promotion_start_date == current_date

    catalogue_predicate = {
        "productPredicate": {"ids": [product_id]},
    }

    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        catalogue_predicate,
        discount_type,
        discount_value,
        promotion_rule_name,
        channel_id,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id

    # Step 2 - Get product and check if it is on promotion

    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    assert product_data["id"] == product_id
    assert product_data["pricing"]["onSale"] is True
    variant_data = product_data["variants"][0]
    variant_id = product_data["variants"][0]["id"]
    assert variant_id == product_variant_id
    assert variant_data["pricing"]["onSale"] is True
