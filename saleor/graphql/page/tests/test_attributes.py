from unittest.mock import ANY

import graphene

from ....page.error_codes import PageErrorCode
from ...tests.utils import assert_no_permission, get_graphql_content

PAGE_ASSIGN_ATTR_QUERY = """
    mutation assign($pageTypeId: ID!, $attributeIds: [ID!]!) {
      pageAttributeAssign(pageTypeId: $pageTypeId, attributeIds: $attributeIds) {
        pageErrors {
          field
          code
          message
          attributes
        }
        pageType {
          id
          attributes {
            id
          }
        }
      }
    }
"""


def test_assign_attributes_to_page_type_by_staff(
    staff_api_client,
    permission_manage_page_types_and_attributes,
    page_type,
    author_page_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    page_type_attr_count = page_type.page_attributes.count()

    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [author_page_attr_id],
    }

    # when
    response = staff_api_client.post_graphql(PAGE_ASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageAttributeAssign"]
    errors = data["pageErrors"]

    assert not errors
    assert len(data["pageType"]["attributes"]) == page_type_attr_count + 1
    assert author_page_attr_id in {
        attr["id"] for attr in data["pageType"]["attributes"]
    }


def test_assign_attributes_to_page_type_by_app(
    app_api_client,
    permission_manage_page_types_and_attributes,
    page_type,
    author_page_attribute,
):
    # given
    app = app_api_client.app
    app.permissions.add(permission_manage_page_types_and_attributes)

    page_type_attr_count = page_type.page_attributes.count()

    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [author_page_attr_id],
    }

    # when
    response = app_api_client.post_graphql(PAGE_ASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageAttributeAssign"]
    errors = data["pageErrors"]

    assert not errors
    assert len(data["pageType"]["attributes"]) == page_type_attr_count + 1
    assert author_page_attr_id in {
        attr["id"] for attr in data["pageType"]["attributes"]
    }


def test_assign_attributes_to_page_type_by_staff_no_perm(
    staff_api_client,
    permission_manage_page_types_and_attributes,
    page_type,
    author_page_attribute,
):
    # given
    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [author_page_attr_id],
    }

    # when
    response = staff_api_client.post_graphql(PAGE_ASSIGN_ATTR_QUERY, variables)

    # then
    assert_no_permission(response)


def test_assign_attributes_to_page_type_by_app_no_perm(
    app_api_client,
    permission_manage_page_types_and_attributes,
    page_type,
    author_page_attribute,
):
    # given
    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [author_page_attr_id],
    }

    # when
    response = app_api_client.post_graphql(PAGE_ASSIGN_ATTR_QUERY, variables)

    # then
    assert_no_permission(response)


def test_assign_attributes_to_page_type_not_page_attribute(
    staff_api_client,
    permission_manage_page_types_and_attributes,
    page_type,
    author_page_attribute,
    color_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    page_type_attr_count = page_type.page_attributes.count()

    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [author_page_attr_id, color_attribute_id],
    }

    # when
    response = staff_api_client.post_graphql(PAGE_ASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageAttributeAssign"]
    errors = data["pageErrors"]

    assert not data["pageType"]
    page_type.refresh_from_db()
    assert page_type.page_attributes.count() == page_type_attr_count
    assert len(errors) == 1
    assert errors[0]["field"] == "attributeIds"
    assert errors[0]["code"] == PageErrorCode.INVALID.name
    assert len(errors[0]["attributes"]) == 1
    assert errors[0]["attributes"] == [color_attribute_id]


def test_assign_attributes_to_page_type_attribute_already_assigned(
    staff_api_client,
    permission_manage_page_types_and_attributes,
    page_type,
    author_page_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    page_type_attr_count = page_type.page_attributes.count()

    assigned_attr = page_type.page_attributes.first()
    assigned_attr_id = graphene.Node.to_global_id("Attribute", assigned_attr.pk)
    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [author_page_attr_id, assigned_attr_id],
    }

    # when
    response = staff_api_client.post_graphql(PAGE_ASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageAttributeAssign"]
    errors = data["pageErrors"]

    assert not data["pageType"]
    page_type.refresh_from_db()
    assert page_type.page_attributes.count() == page_type_attr_count
    assert len(errors) == 1
    assert errors[0]["field"] == "attributeIds"
    assert errors[0]["code"] == PageErrorCode.ATTRIBUTE_ALREADY_ASSIGNED.name
    assert len(errors[0]["attributes"]) == 1
    assert errors[0]["attributes"] == [assigned_attr_id]


def test_assign_attributes_to_page_type_multiple_error_returned(
    staff_api_client,
    permission_manage_page_types_and_attributes,
    page_type,
    author_page_attribute,
    color_attribute,
):
    """Ensure that when multiple errors ocurred all will br returned. """
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    page_type_attr_count = page_type.page_attributes.count()

    assigned_attr = page_type.page_attributes.first()
    assigned_attr_id = graphene.Node.to_global_id("Attribute", assigned_attr.pk)
    author_page_attr_id = graphene.Node.to_global_id(
        "Attribute", author_page_attribute.pk
    )
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [author_page_attr_id, assigned_attr_id, color_attribute_id],
    }

    # when
    response = staff_api_client.post_graphql(PAGE_ASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageAttributeAssign"]
    errors = data["pageErrors"]

    assert not data["pageType"]
    page_type.refresh_from_db()
    assert page_type.page_attributes.count() == page_type_attr_count
    assert len(errors) == 2
    expected_errors = [
        {
            "field": "attributeIds",
            "code": PageErrorCode.ATTRIBUTE_ALREADY_ASSIGNED.name,
            "attributes": [assigned_attr_id],
            "message": ANY,
        },
        {
            "field": "attributeIds",
            "code": PageErrorCode.INVALID.name,
            "attributes": [color_attribute_id],
            "message": ANY,
        },
    ]
    assert len(errors) == len(expected_errors)
    for error in errors:
        assert error in expected_errors


PAGE_UNASSIGN_ATTR_QUERY = """
    mutation PageAttributeUnassign(
        $pageTypeId: ID!, $attributeIds: [ID!]!
    ) {
        pageAttributeUnassign(
            pageTypeId: $pageTypeId, attributeIds: $attributeIds
        ) {
            pageType {
                id
                attributes {
                    id
                }
            }
            pageErrors {
                field
                code
                message
                attributes
            }
        }
    }
"""


def test_unassign_attributes_from_page_type_by_staff(
    staff_api_client, page_type, permission_manage_page_types_and_attributes
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_page_types_and_attributes)

    attr_count = page_type.page_attributes.count()
    attr_to_unassign = page_type.page_attributes.first()
    attr_to_unassign_id = graphene.Node.to_global_id("Attribute", attr_to_unassign.pk)

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [attr_to_unassign_id],
    }

    # when
    response = staff_api_client.post_graphql(PAGE_UNASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageAttributeUnassign"]
    errors = data["pageErrors"]

    assert not errors
    assert len(data["pageType"]["attributes"]) == attr_count - 1
    assert attr_to_unassign_id not in {
        attr["id"] for attr in data["pageType"]["attributes"]
    }


def test_unassign_attributes_from_page_type_by_staff_no_perm(
    staff_api_client, page_type
):
    # given
    attr_to_unassign = page_type.page_attributes.first()
    attr_to_unassign_id = graphene.Node.to_global_id("Attribute", attr_to_unassign.pk)

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [attr_to_unassign_id],
    }

    # when
    response = staff_api_client.post_graphql(PAGE_UNASSIGN_ATTR_QUERY, variables)

    # then
    assert_no_permission(response)


def test_unassign_attributes_from_page_type_by_app(
    app_api_client, page_type, permission_manage_page_types_and_attributes
):
    # given
    app = app_api_client.app
    app.permissions.add(permission_manage_page_types_and_attributes)

    attr_count = page_type.page_attributes.count()
    attr_to_unassign = page_type.page_attributes.first()
    attr_to_unassign_id = graphene.Node.to_global_id("Attribute", attr_to_unassign.pk)

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [attr_to_unassign_id],
    }

    # when
    response = app_api_client.post_graphql(PAGE_UNASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageAttributeUnassign"]
    errors = data["pageErrors"]

    assert not errors
    assert len(data["pageType"]["attributes"]) == attr_count - 1
    assert attr_to_unassign_id not in {
        attr["id"] for attr in data["pageType"]["attributes"]
    }


def test_unassign_attributes_from_page_type_by_app_no_perm(app_api_client, page_type):
    # given
    attr_to_unassign = page_type.page_attributes.first()
    attr_to_unassign_id = graphene.Node.to_global_id("Attribute", attr_to_unassign.pk)

    variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [attr_to_unassign_id],
    }

    # when
    response = app_api_client.post_graphql(PAGE_UNASSIGN_ATTR_QUERY, variables)

    # then
    assert_no_permission(response)
