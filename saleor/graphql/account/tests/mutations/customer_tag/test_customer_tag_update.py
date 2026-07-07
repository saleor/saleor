import graphene

from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TAG_UPDATE_MUTATION = """
    mutation CustomerTagUpdate($id: ID!, $input: CustomerTagInput!) {
        customerTagUpdate(id: $id, input: $input) {
            customerTag {
                id
                name
                slug
                description
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_customer_tag_update(
    staff_api_client, permission_manage_customer_tags, customer_tag
):
    # given
    new_name = "VIP Gold"
    new_description = "Top-tier customers."
    variables = {
        "id": graphene.Node.to_global_id("CustomerTag", customer_tag.pk),
        "input": {"name": new_name, "description": new_description},
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_UPDATE_MUTATION,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagUpdate"]
    assert data["errors"] == []
    assert data["customerTag"]["name"] == new_name
    assert data["customerTag"]["description"] == new_description
    # slug is preserved on update
    assert data["customerTag"]["slug"] == customer_tag.slug
    customer_tag.refresh_from_db()
    assert customer_tag.name == new_name


def test_customer_tag_update_no_permission(staff_api_client, customer_tag):
    # given
    variables = {
        "id": graphene.Node.to_global_id("CustomerTag", customer_tag.pk),
        "input": {"name": "VIP Gold"},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TAG_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)
