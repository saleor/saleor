import graphene

from ......account.error_codes import CustomerTagErrorCode
from ......account.models import CustomerTag
from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TAG_DELETE_MUTATION = """
    mutation CustomerTagDelete($id: ID!, $force: Boolean) {
        customerTagDelete(id: $id, force: $force) {
            customerTag {
                id
                name
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_customer_tag_delete(
    staff_api_client, permission_manage_customer_tags, customer_tag
):
    # given
    tag_id = graphene.Node.to_global_id("CustomerTag", customer_tag.pk)
    variables = {"id": tag_id}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagDelete"]
    assert data["errors"] == []
    assert data["customerTag"]["name"] == customer_tag.name
    assert not CustomerTag.objects.filter(pk=customer_tag.pk).exists()


def test_customer_tag_delete_prevented_when_assigned(
    staff_api_client,
    permission_manage_customer_tags,
    customer_tag,
    customer_user_with_tag,
):
    # given
    tag_id = graphene.Node.to_global_id("CustomerTag", customer_tag.pk)
    variables = {"id": tag_id, "force": False}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagDelete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CustomerTagErrorCode.CANNOT_DELETE.name
    assert CustomerTag.objects.filter(pk=customer_tag.pk).exists()


def test_customer_tag_delete_force_when_assigned(
    staff_api_client,
    permission_manage_customer_tags,
    customer_tag,
    customer_user_with_tag,
):
    # given
    tag_id = graphene.Node.to_global_id("CustomerTag", customer_tag.pk)
    variables = {"id": tag_id, "force": True}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagDelete"]
    assert data["errors"] == []
    assert not CustomerTag.objects.filter(pk=customer_tag.pk).exists()
    # the assignment is removed together with the tag
    assert customer_user_with_tag.tags.count() == 0


def test_customer_tag_delete_no_permission(staff_api_client, customer_tag):
    # given
    tag_id = graphene.Node.to_global_id("CustomerTag", customer_tag.pk)
    variables = {"id": tag_id}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TAG_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)
