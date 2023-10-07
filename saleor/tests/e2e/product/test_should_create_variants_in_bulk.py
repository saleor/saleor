import pytest

from ..attributes.utils import attribute_create
from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_variants_in_bulk,
    get_product,
    update_product_type_assignment_attribute,
)


def prepare_attributes_and_product_type(e2e_staff_api_client):
    attribute_product = attribute_create(
        e2e_staff_api_client,
        input_type="DROPDOWN",
        name="Flavor",
        slug="flavor",
        type="PRODUCT_TYPE",
        value_required=True,
    )
    attribute_product_id = attribute_product["id"]

    attribute_variant = attribute_create(
        e2e_staff_api_client,
        input_type="DROPDOWN",
        name="Size",
        slug="size",
        type="PRODUCT_TYPE",
        value_required=True,
        is_variant_only=True,
    )
    attribute_variant_id = attribute_variant["id"]

    product_type_data = create_product_type(
        e2e_staff_api_client,
        has_variants=True,
        product_attributes=[attribute_product_id],
        variant_attributes=[attribute_variant_id],
    )
    product_type_id = product_type_data["id"]

    operations = [{"id": attribute_variant_id, "variantSelection": True}]
    updated_variant_attribute = update_product_type_assignment_attribute(
        e2e_staff_api_client, product_type_id, operations
    )
    assert (
        updated_variant_attribute["assignedVariantAttributes"][0]["variantSelection"]
        is True
    )
    assert (
        updated_variant_attribute["assignedVariantAttributes"][0]["attribute"]["id"]
        == attribute_variant_id
    )
    return attribute_product_id, attribute_variant_id, product_type_id


@pytest.mark.e2e
def test_should_create_product_with_few_variants_core_0301(
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        warehouse_id,
        channel_id,
        channel_slug,
        _shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

    (
        attribute_product_id,
        attribute_variant_id,
        product_type_id,
    ) = prepare_attributes_and_product_type(e2e_staff_api_client)

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    # Step 1 - Create product with attribute
    attributes = [
        {
            "id": attribute_product_id,
            "dropdown": {"value": "orange"},
        }
    ]
    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
        attributes=attributes,
    )
    product_id = product_data["id"]
    attribute = product_data["attributes"][0]
    assert attribute["attribute"]["id"] == attribute_product_id
    assert attribute["values"][0]["name"] == "orange"

    # Step 2 - Update product channel listing

    create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        channel_id,
    )

    # Step 3 - Create variants with attributes, channel listing and stock in bulk
    first_variant_name = "250ml"
    first_variant_price = 1.99
    second_variant_name = "250ml"
    second_variant_price = 1.99

    variants = [
        {
            "attributes": [
                {"id": attribute_variant_id, "values": [first_variant_name]}
            ],
            "name": first_variant_name,
            "channelListings": [
                {"channelId": channel_id, "price": first_variant_price}
            ],
            "stocks": [{"warehouse": warehouse_id, "quantity": 99}],
        },
        {
            "attributes": [
                {"id": attribute_variant_id, "values": [second_variant_name]}
            ],
            "name": second_variant_name,
            "channelListings": [
                {"channelId": channel_id, "price": second_variant_price}
            ],
            "stocks": [{"warehouse": warehouse_id, "quantity": 20}],
        },
    ]
    create_variants_in_bulk(e2e_staff_api_client, product_id, variants)

    # Step 4 - Check product variants
    product = get_product(e2e_staff_api_client, product_id, channel_slug)
    first_variant = product["variants"][0]
    second_variant = product["variants"][1]

    assert first_variant["attributes"][0]["attribute"]["id"] == attribute_variant_id
    assert first_variant["attributes"][0]["values"][0]["name"] == first_variant_name
    assert first_variant["channelListings"][0]["channel"]["id"] == channel_id
    assert first_variant["channelListings"][0]["price"]["amount"] == first_variant_price
    assert first_variant["stocks"][0]["warehouse"]["id"] == warehouse_id

    assert second_variant["attributes"][0]["attribute"]["id"] == attribute_variant_id
    assert second_variant["attributes"][0]["values"][0]["name"] == second_variant_name
    assert second_variant["channelListings"][0]["channel"]["id"] == channel_id
    assert (
        second_variant["channelListings"][0]["price"]["amount"] == second_variant_price
    )
    assert second_variant["stocks"][0]["warehouse"]["id"] == warehouse_id
