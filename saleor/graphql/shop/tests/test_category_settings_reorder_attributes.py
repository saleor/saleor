import graphene

from ....attribute.models import AttributeCategory
from ...tests.utils import assert_no_permission, get_graphql_content

CATEGORY_SETTINGS_REORDER_ATTRIBUTES_MUTATION = """
    mutation CategorySettingsReorderAttributes($moves: [ReorderInput]!) {
        categorySettingsReorderAttributes(moves: $moves) {
            categorySettings {
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


def test_category_settings_reorder_attrs_by_staff(
    staff_api_client,
    site_settings_with_category_attributes,
    size_page_attribute,
    tag_page_attribute,
    page_type_product_reference_attribute,
    page_type_page_reference_attribute,
    permission_manage_settings,
):
    # given
    query = CATEGORY_SETTINGS_REORDER_ATTRIBUTES_MUTATION
    site_settings = site_settings_with_category_attributes
    AttributeCategory.objects.bulk_create(
        [
            AttributeCategory(site_settings=site_settings, attribute=attr)
            for attr in [
                tag_page_attribute,
                page_type_product_reference_attribute,
                page_type_page_reference_attribute,
            ]
        ]
    )
    variables = {
        "moves": [
            {
                "id": graphene.Node.to_global_id("Attribute", tag_page_attribute.pk),
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
        query, variables, permissions=(permission_manage_settings,)
    )
    content = get_graphql_content(response)

    # then
    expected_order = [
        tag_page_attribute.slug,
        size_page_attribute.slug,
        page_type_page_reference_attribute.slug,
        page_type_product_reference_attribute.slug,
    ]
    data = content["data"]["categorySettingsReorderAttributes"]
    category_settings = data["categorySettings"]

    assert not data["shopErrors"]
    assert [attr["slug"] for attr in category_settings["attributes"]] == expected_order


def test_category_settings_reorder_attrs_by_app(
    app_api_client,
    site_settings_with_category_attributes,
    size_page_attribute,
    tag_page_attribute,
    page_type_product_reference_attribute,
    page_type_page_reference_attribute,
    permission_manage_settings,
):
    # given
    query = CATEGORY_SETTINGS_REORDER_ATTRIBUTES_MUTATION
    site_settings = site_settings_with_category_attributes
    AttributeCategory.objects.bulk_create(
        [
            AttributeCategory(site_settings=site_settings, attribute=attr)
            for attr in [
                tag_page_attribute,
                page_type_product_reference_attribute,
                page_type_page_reference_attribute,
            ]
        ]
    )
    variables = {
        "moves": [
            {
                "id": graphene.Node.to_global_id("Attribute", tag_page_attribute.pk),
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
        query, variables, permissions=(permission_manage_settings,)
    )
    content = get_graphql_content(response)

    # then
    expected_order = [
        tag_page_attribute.slug,
        page_type_product_reference_attribute.slug,
        size_page_attribute.slug,
        page_type_page_reference_attribute.slug,
    ]
    data = content["data"]["categorySettingsReorderAttributes"]
    category_settings = data["categorySettings"]

    assert not data["shopErrors"]
    assert [attr["slug"] for attr in category_settings["attributes"]] == expected_order


def test_category_settings_reorder_attrs_by_customer(
    user_api_client,
    site_settings_with_category_attributes,
    tag_page_attribute,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
):
    # given
    query = CATEGORY_SETTINGS_REORDER_ATTRIBUTES_MUTATION
    site_settings = site_settings_with_category_attributes
    AttributeCategory.objects.bulk_create(
        [
            AttributeCategory(site_settings=site_settings, attribute=attr)
            for attr in [
                tag_page_attribute,
                page_type_product_reference_attribute,
                page_type_page_reference_attribute,
            ]
        ]
    )
    variables = {
        "moves": [
            {
                "id": graphene.Node.to_global_id("Attribute", tag_page_attribute.pk),
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
