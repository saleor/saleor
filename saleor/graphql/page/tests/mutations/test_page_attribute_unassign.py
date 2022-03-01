import graphene

from ....tests.utils import assert_no_permission, get_graphql_content

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
            errors {
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
    errors = data["errors"]

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
    errors = data["errors"]

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
