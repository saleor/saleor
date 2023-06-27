import graphene

from .....account.models import Group
from ....tests.utils import get_graphql_content

GROUP_FEDERATION_QUERY = """
  query GetGroupInFederation($representations: [_Any]) {
    _entities(representations: $representations) {
      __typename
      ... on Group {
        id
        name
      }
    }
  }
"""


def test_staff_query_group_federation(staff_api_client, permission_manage_staff):
    group = Group.objects.create(name="empty group")
    group_id = graphene.Node.to_global_id("Group", group.pk)
    variables = {
        "representations": [
            {
                "__typename": "Group",
                "id": group_id,
            },
        ],
    }

    response = staff_api_client.post_graphql(
        GROUP_FEDERATION_QUERY,
        variables,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Group",
            "id": group_id,
            "name": group.name,
        }
    ]


def test_app_query_group_federation(app_api_client, permission_manage_staff):
    group = Group.objects.create(name="empty group")
    group_id = graphene.Node.to_global_id("Group", group.pk)
    variables = {
        "representations": [
            {
                "__typename": "Group",
                "id": group_id,
            },
        ],
    }

    response = app_api_client.post_graphql(
        GROUP_FEDERATION_QUERY,
        variables,
        permissions=[permission_manage_staff],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Group",
            "id": group_id,
            "name": group.name,
        }
    ]


def test_app_no_permission_query_group_federation(app_api_client):
    group = Group.objects.create(name="empty group")
    group_id = graphene.Node.to_global_id("Group", group.pk)
    variables = {
        "representations": [
            {
                "__typename": "Group",
                "id": group_id,
            },
        ],
    }

    response = app_api_client.post_graphql(GROUP_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_client_query_group_federation(user_api_client):
    group = Group.objects.create(name="empty group")

    group_id = graphene.Node.to_global_id("Group", group.pk)
    variables = {
        "representations": [
            {
                "__typename": "Group",
                "id": group_id,
            },
        ],
    }

    response = user_api_client.post_graphql(GROUP_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_unauthenticated_query_group_federation(api_client):
    group = Group.objects.create(name="empty group")

    group_id = graphene.Node.to_global_id("Group", group.pk)
    variables = {
        "representations": [
            {
                "__typename": "Group",
                "id": group_id,
            },
        ],
    }

    response = api_client.post_graphql(GROUP_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]
