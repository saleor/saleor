import graphene
import pytest

from ....account.models import Group
from ....channel.models import Channel
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_PERMISSION_GROUP_WITH_FILTER = """
query ($filter: PermissionGroupFilterInput ){
    permissionGroups(first: 5, filter: $filter){
        edges{
            node{
                id
                name
                permissions{
                    name
                    code
                }
                users {
                    email
                }
                userCanManage
            }
        }
    }
}
"""


@pytest.mark.parametrize(
    "permission_group_filter, count",
    (({"search": "Manage user groups"}, 1), ({"search": "Manage"}, 2), ({}, 3)),
)
def test_permission_groups_query(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_filter,
    count,
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = QUERY_PERMISSION_GROUP_WITH_FILTER

    Group.objects.bulk_create(
        [Group(name="Manage product."), Group(name="Remove product.")]
    )

    variables = {"filter": permission_group_filter}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroups"]["edges"]

    assert len(data) == count


def test_permission_groups_query_with_filter_by_ids(
    permission_group_manage_users,
    permission_manage_staff,
    staff_api_client,
):
    # given
    query = QUERY_PERMISSION_GROUP_WITH_FILTER
    variables = {
        "filter": {
            "ids": [
                graphene.Node.to_global_id("Group", permission_group_manage_users.pk)
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["permissionGroups"]["edges"]
    assert len(data) == 1


def test_permission_groups_no_permission_to_perform(
    permission_group_manage_users,
    permission_manage_staff,
    staff_api_client,
):
    query = QUERY_PERMISSION_GROUP_WITH_FILTER

    variables = {"filter": {"search": "Manage user groups"}}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


QUERY_PERMISSION_GROUP_WITH_SORT = """
query ($sort_by: PermissionGroupSortingInput!) {
    permissionGroups(first:5, sortBy: $sort_by) {
        edges{
            node{
                name
            }
        }
    }
}
"""


@pytest.mark.parametrize(
    "permission_group_sort, result",
    (
        (
            {"field": "NAME", "direction": "ASC"},
            ["Add", "Manage user group.", "Remove"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["Remove", "Manage user group.", "Add"],
        ),
    ),
)
def test_permission_group_with_sort(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
    permission_group_sort,
    result,
):
    staff_user.user_permissions.add(permission_manage_staff)
    query = QUERY_PERMISSION_GROUP_WITH_SORT

    Group.objects.bulk_create([Group(name="Add"), Group(name="Remove")])

    variables = {"sort_by": permission_group_sort}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroups"]["edges"]

    for order, group_name in enumerate(result):
        assert data[order]["node"]["name"] == group_name


QUERY_PERMISSION_GROUP = """
query ($id: ID!){
    permissionGroup(id: $id){
        id
        name
        permissions {
            name
            code
        }
        users{
            email
        }
        userCanManage
        accessibleChannels {
            slug
        }
        restrictedAccessToChannels
    }
}
"""


def test_permission_group_query(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    permission_manage_users,
    staff_api_client,
):
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
    group = permission_group_manage_users
    query = QUERY_PERMISSION_GROUP

    group_staff_user = group.user_set.first()

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroup"]

    assert data["name"] == group.name
    assert len(data["users"]) == 1
    assert data["users"][0]["email"] == group_staff_user.email
    result_permissions = {permission["name"] for permission in data["permissions"]}
    assert (
        set(group.permissions.all().values_list("name", flat=True))
        == result_permissions
    )
    permissions_codes = {
        permission["code"].lower() for permission in data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )
    assert data["userCanManage"] is True


def test_permission_group_query_user_cannot_manage(
    permission_group_manage_users,
    staff_user,
    permission_manage_staff,
    staff_api_client,
):
    staff_user.user_permissions.add(permission_manage_staff)
    group = permission_group_manage_users
    query = QUERY_PERMISSION_GROUP

    group_staff_user = group.user_set.first()

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["permissionGroup"]

    assert data["name"] == group.name
    assert len(data["users"]) == 1
    assert data["users"][0]["email"] == group_staff_user.email
    result_permissions = {permission["name"] for permission in data["permissions"]}
    assert (
        set(group.permissions.all().values_list("name", flat=True))
        == result_permissions
    )
    permissions_codes = {
        permission["code"].lower() for permission in data["permissions"]
    }
    assert (
        set(group.permissions.all().values_list("codename", flat=True))
        == permissions_codes
    )
    assert data["userCanManage"] is False


def test_permission_group_no_permission_to_perform(
    permission_group_manage_users,
    permission_manage_staff,
    staff_api_client,
):
    group = permission_group_manage_users
    query = QUERY_PERMISSION_GROUP

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_query_permission_group_by_invalid_id(
    staff_api_client,
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_staff,
):
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_PERMISSION_GROUP, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["permissionGroup"] is None


def test_query_permission_group_with_invalid_object_type(
    staff_api_client,
    staff_user,
    permission_group_manage_users,
    permission_manage_staff,
    permission_manage_users,
):
    staff_user.user_permissions.add(permission_manage_staff, permission_manage_users)
    variables = {
        "id": graphene.Node.to_global_id("Order", permission_group_manage_users.pk)
    }
    response = staff_api_client.post_graphql(QUERY_PERMISSION_GROUP, variables)
    content = get_graphql_content(response)
    assert content["data"]["permissionGroup"] is None


def test_query_permission_group_without_restricted_access_to_channels(
    staff_api_client,
    staff_user,
    permission_group_all_perms_all_channels,
    channel_USD,
    channel_PLN,
):
    # given
    group = permission_group_all_perms_all_channels
    group.user_set.add(staff_user)

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}

    # when
    response = staff_api_client.post_graphql(QUERY_PERMISSION_GROUP, variables)

    # then

    content = get_graphql_content(response)
    group_data = content["data"]["permissionGroup"]
    assert group_data["name"] == group.name
    assert group_data["restrictedAccessToChannels"] is False
    assert len(group_data["accessibleChannels"]) == 2


def test_query_permission_group_with_restricted_access_to_channels(
    staff_api_client,
    staff_user,
    permission_group_all_perms_channel_USD_only,
    channel_USD,
    channel_PLN,
):
    # given
    group = permission_group_all_perms_channel_USD_only
    group.user_set.add(staff_user)

    assert Channel.objects.count() > 1

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}

    # when
    response = staff_api_client.post_graphql(QUERY_PERMISSION_GROUP, variables)

    # then

    content = get_graphql_content(response)
    group_data = content["data"]["permissionGroup"]
    assert group_data["name"] == group.name
    assert group_data["restrictedAccessToChannels"] is True
    assert len(group_data["accessibleChannels"]) == 1
    assert group_data["accessibleChannels"][0]["slug"] == channel_USD.slug


def test_query_permission_group_with_restricted_access_to_channels_no_channels_assigned(
    staff_api_client,
    staff_user,
    permission_group_all_perms_without_any_channel,
    channel_USD,
    channel_PLN,
):
    # given
    group = permission_group_all_perms_without_any_channel
    group.user_set.add(staff_user)

    assert Channel.objects.count() > 1

    variables = {"id": graphene.Node.to_global_id("Group", group.id)}

    # when
    response = staff_api_client.post_graphql(QUERY_PERMISSION_GROUP, variables)

    # then

    content = get_graphql_content(response)
    group_data = content["data"]["permissionGroup"]
    assert group_data["name"] == group.name
    assert group_data["restrictedAccessToChannels"] is True
    assert len(group_data["accessibleChannels"]) == 0
