import graphene

from ....attribute.models import AttributeCollection
from ...tests.utils import assert_no_permission, get_graphql_content

CATEGORY_SETTINGS_REORDER_ATTRIBUTES_MUTATION = """
    mutation CollectionSettingsReorderAttributes($moves: [ReorderInput]!) {
        collectionSettingsReorderAttributes(moves: $moves) {
            collectionAttributeSettings {
                attributes {
                    id
                    slug
                }
            }
            shopErrors {
                code
                field
            }
        }
    }
"""


def test_collection_settings_reorder_attrs_by_staff(
    staff_api_client,
    site_settings_with_collection_attributes,
    size_page_attribute,
    tag_page_attribute,
    page_type_product_reference_attribute,
    page_type_page_reference_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    query = CATEGORY_SETTINGS_REORDER_ATTRIBUTES_MUTATION
    site_settings = site_settings_with_collection_attributes
    AttributeCollection.objects.bulk_create(
        [
            AttributeCollection(site_settings=site_settings, attribute=attr)
            for attr in [
                size_page_attribute,
                page_type_product_reference_attribute,
                page_type_page_reference_attribute,
            ]
        ]
    )
    variables = {
        "moves": [
            {
                "id": graphene.Node.to_global_id("Attribute", size_page_attribute.pk),
                "sortOrder": -1,
            },
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", page_type_product_reference_attribute.pk
                ),
                "sortOrder": +1,
            },
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_page_types_and_attributes,)
    )
    content = get_graphql_content(response)

    # then
    expected_order = [
        size_page_attribute.slug,
        tag_page_attribute.slug,
        page_type_page_reference_attribute.slug,
        page_type_product_reference_attribute.slug,
    ]
    data = content["data"]["collectionSettingsReorderAttributes"]
    collection_settings = data["collectionAttributeSettings"]

    assert not data["shopErrors"]
    assert [
        attr["slug"] for attr in collection_settings["attributes"]
    ] == expected_order


def test_collection_settings_reorder_attrs_by_app(
    app_api_client,
    site_settings_with_collection_attributes,
    size_page_attribute,
    tag_page_attribute,
    page_type_product_reference_attribute,
    page_type_page_reference_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    query = CATEGORY_SETTINGS_REORDER_ATTRIBUTES_MUTATION
    site_settings = site_settings_with_collection_attributes
    AttributeCollection.objects.bulk_create(
        [
            AttributeCollection(site_settings=site_settings, attribute=attr)
            for attr in [
                size_page_attribute,
                page_type_product_reference_attribute,
                page_type_page_reference_attribute,
            ]
        ]
    )
    variables = {
        "moves": [
            {
                "id": graphene.Node.to_global_id("Attribute", size_page_attribute.pk),
                "sortOrder": -1,
            },
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", page_type_product_reference_attribute.pk
                ),
                "sortOrder": -1,
            },
        ]
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_page_types_and_attributes,)
    )
    content = get_graphql_content(response)

    # then
    expected_order = [
        size_page_attribute.slug,
        page_type_product_reference_attribute.slug,
        tag_page_attribute.slug,
        page_type_page_reference_attribute.slug,
    ]
    data = content["data"]["collectionSettingsReorderAttributes"]
    collection_settings = data["collectionAttributeSettings"]

    assert not data["shopErrors"]
    assert [
        attr["slug"] for attr in collection_settings["attributes"]
    ] == expected_order


def test_collection_settings_reorder_attrs_by_customer(
    user_api_client,
    site_settings_with_collection_attributes,
    size_page_attribute,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
):
    # given
    query = CATEGORY_SETTINGS_REORDER_ATTRIBUTES_MUTATION
    site_settings = site_settings_with_collection_attributes
    AttributeCollection.objects.bulk_create(
        [
            AttributeCollection(site_settings=site_settings, attribute=attr)
            for attr in [
                size_page_attribute,
                page_type_product_reference_attribute,
                page_type_page_reference_attribute,
            ]
        ]
    )
    variables = {
        "moves": [
            {
                "id": graphene.Node.to_global_id("Attribute", size_page_attribute.pk),
                "sortOrder": -1,
            },
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", page_type_product_reference_attribute.pk
                ),
                "sortOrder": +1,
            },
        ]
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)
