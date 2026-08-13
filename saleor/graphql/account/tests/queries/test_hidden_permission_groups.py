import graphene
import pytest
from django.conf import settings

from .....account.error_codes import PermissionGroupErrorCode
from .....account.models import Group
from ....tests.utils import get_graphql_content

HIDDEN_GROUP_NAME = "Hidden group"

PERMISSION_GROUPS_QUERY = """
    query {
        permissionGroups(first: 20) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""

PERMISSION_GROUP_QUERY = """
    query PermissionGroup($id: ID!) {
        permissionGroup(id: $id) {
            id
            name
        }
    }
"""

USER_GROUPS_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            permissionGroups {
                name
            }
            editableGroups {
                name
            }
        }
    }
"""

GROUP_FEDERATION_QUERY = """
    query GetGroupInFederation($representations: [_Any!]!) {
        _entities(representations: $representations) {
            __typename
            ... on Group {
                id
                name
            }
        }
    }
"""


@pytest.fixture
def hidden_group(db):
    return Group.objects.create(
        name=HIDDEN_GROUP_NAME, restricted_access_to_channels=False
    )


@pytest.fixture
def hide_group_names(settings):
    settings.HIDDEN_PERMISSION_GROUP_NAMES = [HIDDEN_GROUP_NAME]
    return settings.HIDDEN_PERMISSION_GROUP_NAMES


def test_permission_groups_excludes_hidden_group(
    staff_api_client,
    permission_manage_staff,
    hidden_group,
    permission_group_manage_users,
    hide_group_names,
):
    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUPS_QUERY,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    returned_names = {
        edge["node"]["name"] for edge in content["data"]["permissionGroups"]["edges"]
    }
    assert returned_names == {permission_group_manage_users.name}


def test_permission_groups_returns_group_when_not_hidden(
    staff_api_client,
    permission_manage_staff,
    hidden_group,
    permission_group_manage_users,
):
    """Without the setting the group is returned as any other group."""
    # given
    assert settings.HIDDEN_PERMISSION_GROUP_NAMES == []

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUPS_QUERY,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    returned_names = {
        edge["node"]["name"] for edge in content["data"]["permissionGroups"]["edges"]
    }
    assert returned_names == {hidden_group.name, permission_group_manage_users.name}


def test_permission_group_by_id_returns_none_for_hidden_group(
    staff_api_client,
    permission_manage_staff,
    hidden_group,
    hide_group_names,
):
    # given
    variables = {"id": graphene.Node.to_global_id("Group", hidden_group.pk)}

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_QUERY,
        variables,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["permissionGroup"] is None


def test_user_permission_groups_exclude_hidden_group(
    staff_api_client,
    permission_manage_staff,
    permission_manage_users,
    hidden_group,
    permission_group_manage_users,
    hide_group_names,
):
    # given
    user = staff_api_client.user
    user.groups.add(hidden_group, permission_group_manage_users)
    variables = {"id": graphene.Node.to_global_id("User", user.pk)}

    # when
    response = staff_api_client.post_graphql(
        USER_GROUPS_QUERY,
        variables,
        permissions=[permission_manage_staff, permission_manage_users],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert [group["name"] for group in data["permissionGroups"]] == [
        permission_group_manage_users.name
    ]
    assert HIDDEN_GROUP_NAME not in [group["name"] for group in data["editableGroups"]]


def test_group_federation_excludes_hidden_group(
    staff_api_client,
    permission_manage_staff,
    hidden_group,
    hide_group_names,
):
    # given
    group_id = graphene.Node.to_global_id("Group", hidden_group.pk)
    variables = {"representations": [{"__typename": "Group", "id": group_id}]}

    # when
    response = staff_api_client.post_graphql(
        GROUP_FEDERATION_QUERY,
        variables,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


PERMISSION_GROUP_UPDATE_MUTATION = """
    mutation PermissionGroupUpdate($id: ID!, $input: PermissionGroupUpdateInput!) {
        permissionGroupUpdate(id: $id, input: $input) {
            group {
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

PERMISSION_GROUP_DELETE_MUTATION = """
    mutation PermissionGroupDelete($id: ID!) {
        permissionGroupDelete(id: $id) {
            group {
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

PERMISSION_GROUP_CREATE_MUTATION = """
    mutation PermissionGroupCreate($input: PermissionGroupCreateInput!) {
        permissionGroupCreate(input: $input) {
            group {
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


def test_permission_group_update_hidden_group_fails(
    staff_api_client,
    permission_manage_staff,
    hidden_group,
    hide_group_names,
):
    # given
    new_name = "New name"
    variables = {
        "id": graphene.Node.to_global_id("Group", hidden_group.pk),
        "input": {"name": new_name},
    }

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION,
        variables,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupUpdate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == PermissionGroupErrorCode.NOT_FOUND.name
    hidden_group.refresh_from_db(fields=("name",))
    assert hidden_group.name == HIDDEN_GROUP_NAME


def test_permission_group_delete_hidden_group_fails(
    staff_api_client,
    permission_manage_staff,
    hidden_group,
    hide_group_names,
):
    # given
    variables = {"id": graphene.Node.to_global_id("Group", hidden_group.pk)}

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupDelete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == PermissionGroupErrorCode.NOT_FOUND.name
    assert Group.objects.filter(pk=hidden_group.pk).exists() is True


def test_permission_group_create_with_hidden_name_fails(
    staff_api_client,
    permission_manage_staff,
    hide_group_names,
):
    # given
    assert Group.objects.filter(name=HIDDEN_GROUP_NAME).exists() is False
    variables = {"input": {"name": HIDDEN_GROUP_NAME, "addPermissions": []}}

    # when
    response = staff_api_client.post_graphql(
        PERMISSION_GROUP_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["permissionGroupCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["code"] == PermissionGroupErrorCode.UNIQUE.name
    assert Group.objects.filter(name=HIDDEN_GROUP_NAME).exists() is False
