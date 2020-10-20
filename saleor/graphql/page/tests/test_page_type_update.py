from unittest.mock import ANY

import graphene

from ....page.error_codes import PageErrorCode
from ....page.models import PageType
from ...tests.utils import assert_no_permission, get_graphql_content

PAGE_TYPE_UPDATE_MUTATION = """
    mutation PageTypeUpdate(
        $id: ID!, $input: PageTypeUpdateInput!
    ) {
        pageTypeUpdate(id: $id, input: $input) {
            pageType {
                id
                name
                slug
                attributes {
                    slug
                }
            }
            pageErrors {
                code
                field
                message
                attributes
            }
        }
    }
"""


def test_page_type_update_as_staff(
    staff_api_client,
    page_type,
    permission_manage_page_types_and_attributes,
    author_page_attribute,
    size_page_attribute,
    tag_page_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    slug = "new-slug"
    name = "new-name"

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {
            "slug": slug,
            "name": name,
            "addAttributes": [
                graphene.Node.to_global_id("Attribute", author_page_attribute.pk)
            ],
            "removeAttributes": [
                graphene.Node.to_global_id("Attribute", size_page_attribute.pk)
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeUpdate"]
    errors = data["pageErrors"]
    page_type_data = data["pageType"]

    page_type.refresh_from_db()
    assert not errors
    assert page_type_data["name"] == name
    assert page_type_data["slug"] == slug
    assert {attr["slug"] for attr in page_type_data["attributes"]} == {
        tag_page_attribute.slug,
        author_page_attribute.slug,
    }


def test_page_type_update_as_staff_no_perm(staff_api_client, page_type):
    # given
    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {"name": "New page type name"},
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_page_type_update_as_app(
    staff_api_client,
    page_type,
    permission_manage_page_types_and_attributes,
    author_page_attribute,
    size_page_attribute,
    tag_page_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    slug = "new-slug"
    name = "new-name"

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {
            "slug": slug,
            "name": name,
            "addAttributes": [
                graphene.Node.to_global_id("Attribute", author_page_attribute.pk)
            ],
            "removeAttributes": [
                graphene.Node.to_global_id("Attribute", size_page_attribute.pk)
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeUpdate"]
    errors = data["pageErrors"]
    page_type_data = data["pageType"]

    page_type.refresh_from_db()
    assert not errors
    assert page_type_data["name"] == name
    assert page_type_data["slug"] == slug
    assert {attr["slug"] for attr in page_type_data["attributes"]} == {
        tag_page_attribute.slug,
        author_page_attribute.slug,
    }


def test_page_type_update_as_app_no_perm(app_api_client, page_type):
    # given
    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {"name": "New page type name"},
    }

    # when
    response = app_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_page_type_update_duplicated_attributes(
    staff_api_client,
    page_type,
    permission_manage_page_types_and_attributes,
    author_page_attribute,
    size_page_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )
    size_page_att_id = graphene.Node.to_global_id("Attribute", size_page_attribute.pk)

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {
            "addAttributes": [author_page_attr_id],
            "removeAttributes": [author_page_attr_id, size_page_att_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeUpdate"]
    errors = data["pageErrors"]
    page_type_data = data["pageType"]

    assert not page_type_data
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [author_page_attr_id]


def test_page_type_update_not_valid_attributes(
    staff_api_client,
    page_type,
    permission_manage_page_types_and_attributes,
    author_page_attribute,
    size_page_attribute,
    color_attribute,
    weight_attribute,
    size_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {
            "addAttributes": [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in [author_page_attribute, color_attribute]
            ],
            "removeAttributes": [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in [size_page_attribute, weight_attribute, size_attribute]
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeUpdate"]
    errors = data["pageErrors"]
    page_type_data = data["pageType"]

    assert not page_type_data
    assert len(errors) == 2
    expected_errors = [
        {
            "code": PageErrorCode.INVALID.name,
            "field": "addAttributes",
            "message": ANY,
            "attributes": [graphene.Node.to_global_id("Attribute", color_attribute.pk)],
        },
        {
            "code": PageErrorCode.INVALID.name,
            "field": "removeAttributes",
            "message": ANY,
            "attributes": [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in [weight_attribute, size_attribute]
            ],
        },
    ]
    for error in errors:
        assert error in expected_errors


def test_page_type_update_empty_slug(
    staff_api_client, page_type, permission_manage_page_types_and_attributes
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {"name": "New page type name", "slug": ""},
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeUpdate"]
    errors = data["pageErrors"]
    page_type_data = data["pageType"]

    assert not page_type_data
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["field"] == "slug"


def test_page_type_update_duplicated_slug(
    staff_api_client, page_type, permission_manage_page_types_and_attributes
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    slug = "duplicated-tag"
    PageType.objects.create(name="Test page type 2", slug=slug)

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {"name": "New page type name", "slug": slug},
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeUpdate"]
    errors = data["pageErrors"]
    page_type_data = data["pageType"]

    assert not page_type_data
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.UNIQUE.name
    assert errors[0]["field"] == "slug"


def test_page_type_update_multiply_errors(
    staff_api_client,
    page_type,
    permission_manage_page_types_and_attributes,
    author_page_attribute,
    size_page_attribute,
    color_attribute,
):
    """Ensure that if multiply errors occurred all will raised."""

    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )
    size_page_att_id = graphene.Node.to_global_id("Attribute", size_page_attribute.pk)

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "input": {
            "slug": "",
            "addAttributes": [author_page_attr_id, color_attribute_id],
            "removeAttributes": [author_page_attr_id, size_page_att_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeUpdate"]
    errors = data["pageErrors"]
    page_type_data = data["pageType"]

    assert not page_type_data
    assert len(errors) == 3
    assert errors[0]["code"] == PageErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [author_page_attr_id]
