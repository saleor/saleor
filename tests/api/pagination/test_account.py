import pytest
from django.contrib.auth import models as auth_models

from ..utils import get_graphql_content


@pytest.fixture
def permission_groups_for_pagination(db):
    return auth_models.Group.objects.bulk_create(
        [
            auth_models.Group(name="Group1"),
            auth_models.Group(name="GroupGroup1"),
            auth_models.Group(name="GroupGroup2"),
            auth_models.Group(name="Group2"),
            auth_models.Group(name="Group3"),
        ]
    )


QUERY_PERMISSION_GROUPS_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: PermissionGroupSortingInput, $filter: PermissionGroupFilterInput
    ){
        permissionGroups (
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            edges {
                node {
                    name
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


@pytest.mark.parametrize(
    "sort_by, permission_groups_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Group1", "Group2", "Group3"]),
        (
            {"field": "NAME", "direction": "DESC"},
            ["GroupGroup2", "GroupGroup1", "Group3"],
        ),
    ],
)
def test_permission_groups_pagination_with_sorting(
    sort_by,
    permission_groups_order,
    staff_api_client,
    permission_manage_staff,
    permission_groups_for_pagination,
):
    page_size = 3

    variables = {"first": page_size, "after": None, "sortBy": sort_by}
    response = staff_api_client.post_graphql(
        QUERY_PERMISSION_GROUPS_PAGINATION,
        variables,
        permissions=[permission_manage_staff],
    )
    content = get_graphql_content(response)
    permission_groups_nodes = content["data"]["permissionGroups"]["edges"]
    assert permission_groups_order[0] == permission_groups_nodes[0]["node"]["name"]
    assert permission_groups_order[1] == permission_groups_nodes[1]["node"]["name"]
    assert permission_groups_order[2] == permission_groups_nodes[2]["node"]["name"]
    assert len(permission_groups_nodes) == page_size


@pytest.mark.parametrize(
    "filter_by, permission_groups_order",
    [
        ({"search": "GroupGroup"}, ["GroupGroup1", "GroupGroup2"]),
        ({"search": "Group1"}, ["Group1", "GroupGroup1"]),
    ],
)
def test_permission_groups_pagination_with_filtering(
    filter_by,
    permission_groups_order,
    staff_api_client,
    permission_manage_staff,
    permission_groups_for_pagination,
):
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(
        QUERY_PERMISSION_GROUPS_PAGINATION,
        variables,
        permissions=[permission_manage_staff],
    )
    content = get_graphql_content(response)
    permission_groups_nodes = content["data"]["permissionGroups"]["edges"]
    assert permission_groups_order[0] == permission_groups_nodes[0]["node"]["name"]
    assert permission_groups_order[1] == permission_groups_nodes[1]["node"]["name"]
    assert len(permission_groups_nodes) == page_size
