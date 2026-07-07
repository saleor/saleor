from unittest.mock import patch

import graphene

from ......account.models import CustomerTag, UserCustomerTag
from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TAG_ASSIGN_MUTATION = """
    mutation CustomerTagAssign($userIds: [ID!]!, $tagIds: [ID!]!) {
        customerTagAssign(userIds: $userIds, tagIds: $tagIds) {
            users {
                id
            }
            customerTags {
                id
                memberCount
            }
            errors {
                field
                code
                message
            }
        }
    }
"""

CUSTOMER_TAG_UNASSIGN_MUTATION = """
    mutation CustomerTagUnassign($userIds: [ID!]!, $tagIds: [ID!]!) {
        customerTagUnassign(userIds: $userIds, tagIds: $tagIds) {
            users {
                id
            }
            customerTags {
                id
                memberCount
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.customer_tag_assigned")
def test_customer_tag_assign(
    mocked_assigned,
    staff_api_client,
    permission_assign_customer_tags,
    customer_user,
    customer_tag,
):
    # given
    user_id = graphene.Node.to_global_id("User", customer_user.pk)
    tag_id = graphene.Node.to_global_id("CustomerTag", customer_tag.pk)
    variables = {"userIds": [user_id], "tagIds": [tag_id]}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_ASSIGN_MUTATION,
        variables,
        permissions=[permission_assign_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagAssign"]
    assert data["errors"] == []
    assert {user["id"] for user in data["users"]} == {user_id}
    assert data["customerTags"][0]["memberCount"] == 1
    assert UserCustomerTag.objects.filter(user=customer_user, tag=customer_tag).exists()
    assert customer_tag.users.count() == 1
    mocked_assigned.assert_called_once_with(customer_user, [customer_tag])


@patch("saleor.plugins.manager.PluginsManager.customer_tag_assigned")
def test_customer_tag_assign_is_idempotent(
    mocked_assigned,
    staff_api_client,
    permission_assign_customer_tags,
    customer_user_with_tag,
    customer_tag,
):
    # given
    user_id = graphene.Node.to_global_id("User", customer_user_with_tag.pk)
    tag_id = graphene.Node.to_global_id("CustomerTag", customer_tag.pk)
    variables = {"userIds": [user_id], "tagIds": [tag_id]}

    # when re-assigning an already-assigned tag
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_ASSIGN_MUTATION,
        variables,
        permissions=[permission_assign_customer_tags],
    )

    # then no duplicate row, no inflated count, no webhook for a no-op
    content = get_graphql_content(response)
    data = content["data"]["customerTagAssign"]
    assert data["errors"] == []
    assert (
        UserCustomerTag.objects.filter(
            user=customer_user_with_tag, tag=customer_tag
        ).count()
        == 1
    )
    assert customer_tag.users.count() == 1
    mocked_assigned.assert_not_called()


def test_customer_tag_assign_no_permission(
    staff_api_client, customer_user, customer_tag
):
    # given
    variables = {
        "userIds": [graphene.Node.to_global_id("User", customer_user.pk)],
        "tagIds": [graphene.Node.to_global_id("CustomerTag", customer_tag.pk)],
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TAG_ASSIGN_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.customer_tag_unassigned")
def test_customer_tag_unassign(
    mocked_unassigned,
    staff_api_client,
    permission_assign_customer_tags,
    customer_user_with_tag,
    customer_tag,
):
    # given
    user_id = graphene.Node.to_global_id("User", customer_user_with_tag.pk)
    tag_id = graphene.Node.to_global_id("CustomerTag", customer_tag.pk)
    variables = {"userIds": [user_id], "tagIds": [tag_id]}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_UNASSIGN_MUTATION,
        variables,
        permissions=[permission_assign_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagUnassign"]
    assert data["errors"] == []
    assert data["customerTags"][0]["memberCount"] == 0
    assert not UserCustomerTag.objects.filter(
        user=customer_user_with_tag, tag=customer_tag
    ).exists()
    assert customer_tag.users.count() == 0
    mocked_unassigned.assert_called_once_with(customer_user_with_tag, [customer_tag])


@patch("saleor.plugins.manager.PluginsManager.customer_tag_unassigned")
def test_customer_tag_unassign_when_not_assigned_is_noop(
    mocked_unassigned,
    staff_api_client,
    permission_assign_customer_tags,
    customer_user,
    customer_tag,
):
    # given a tag that is not assigned to the user
    user_id = graphene.Node.to_global_id("User", customer_user.pk)
    tag_id = graphene.Node.to_global_id("CustomerTag", customer_tag.pk)
    variables = {"userIds": [user_id], "tagIds": [tag_id]}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_UNASSIGN_MUTATION,
        variables,
        permissions=[permission_assign_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagUnassign"]
    assert data["errors"] == []
    assert customer_tag.users.count() == 0
    mocked_unassigned.assert_not_called()


def test_customer_tag_assign_bulk(
    staff_api_client,
    permission_assign_customer_tags,
    customer_users,
    customer_tags,
):
    # given
    user_ids = [graphene.Node.to_global_id("User", user.pk) for user in customer_users]
    tag_ids = [
        graphene.Node.to_global_id("CustomerTag", tag.pk) for tag in customer_tags
    ]
    variables = {"userIds": user_ids, "tagIds": tag_ids}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_ASSIGN_MUTATION,
        variables,
        permissions=[permission_assign_customer_tags],
    )

    # then every (user, tag) pair is assigned exactly once
    content = get_graphql_content(response)
    data = content["data"]["customerTagAssign"]
    assert data["errors"] == []
    expected_count = len(customer_users) * len(customer_tags)
    assert UserCustomerTag.objects.count() == expected_count
    for tag in CustomerTag.objects.all():
        assert tag.users.count() == len(customer_users)
