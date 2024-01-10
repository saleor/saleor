import pytest

from ..attributes.utils import attribute_create
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
    get_product,
)


def prepare_attributes_and_product_type(e2e_staff_api_client):
    attribute_product = attribute_create(
        e2e_staff_api_client,
        input_type="DROPDOWN",
        name="Material",
        slug="material",
        type="PRODUCT_TYPE",
        value_required=True,
    )
    attribute_product_id = attribute_product["id"]

    product_type_data = create_product_type(
        e2e_staff_api_client,
        has_variants=False,
        product_attributes=[attribute_product_id],
    )
    product_type_id = product_type_data["id"]

    return attribute_product_id, product_type_id


@pytest.mark.e2e
def test_should_create_simple_product_core_0302(
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

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]

    (
        attribute_product_id,
        product_type_id,
    ) = prepare_attributes_and_product_type(e2e_staff_api_client)

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    # Step 1 - Create product with attribute
    product_attribute_value = "Leather"
    attributes = [{"id": attribute_product_id, "values": [product_attribute_value]}]

    product_data = create_product(
        e2e_staff_api_client, product_type_id, category_id, "Bag", attributes=attributes
    )
    product_id = product_data["id"]

    # Step 2 - Update product channel listing
    create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        channel_id,
    )

    # Step 3 - Create variant
    variant_price = 23.99

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 15,
        }
    ]
    variant_data = create_product_variant(
        e2e_staff_api_client, product_id, stocks=stocks
    )
    product_variant_id = variant_data["id"]

    # Step 4 - Update variant channel listing
    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        variant_price,
    )

    # Step 5 - Check product and variant data
    product = get_product(e2e_staff_api_client, product_id, channel_slug)
    assert product["attributes"][0]["attribute"]["id"] == attribute_product_id
    assert product["attributes"][0]["values"][0]["name"] == product_attribute_value
    variant = product["variants"][0]
    assert variant["channelListings"][0]["channel"]["id"] == channel_id
    assert variant["channelListings"][0]["price"]["amount"] == float(variant_price)
    assert variant["stocks"][0]["warehouse"]["id"] == warehouse_id
