import pytest

from .....app.models import App
from ....tests.utils import get_graphql_content


@pytest.fixture
def apps_for_pagination():
    apps = App.objects.bulk_create(
        [
            App(name="Account1", is_active=True),
            App(name="AccountAccount1", is_active=True),
            App(name="AccountAccount2", is_active=True),
            App(name="Account2", is_active=True),
            App(name="Account3", is_active=True),
        ]
    )
    return apps


QUERY_APP_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: AppSortingInput, $filter: AppFilterInput
    ){
        apps(
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            edges{
                node{
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
    ("sort_by", "apps_order"),
    [
        ({"field": "NAME", "direction": "ASC"}, ["Account1", "Account2", "Account3"]),
        (
            {"field": "NAME", "direction": "DESC"},
            ["AccountAccount2", "AccountAccount1", "Account3"],
        ),
    ],
)
def test_apps_pagination_with_sorting(
    sort_by,
    apps_order,
    staff_api_client,
    apps_for_pagination,
    permission_manage_apps,
):
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    page_size = 3
    variables = {"first": page_size, "after": None, "sortBy": sort_by}
    response = staff_api_client.post_graphql(
        QUERY_APP_PAGINATION,
        variables,
    )
    content = get_graphql_content(response)
    nodes = content["data"]["apps"]["edges"]
    assert apps_order[0] == nodes[0]["node"]["name"]
    assert apps_order[1] == nodes[1]["node"]["name"]
    assert apps_order[2] == nodes[2]["node"]["name"]
    assert len(nodes) == page_size


@pytest.mark.parametrize(
    ("filter_by", "apps_order"),
    [
        ({"search": "Account"}, ["Account1", "Account2"]),
        ({"search": "AccountAccount"}, ["AccountAccount1", "AccountAccount2"]),
        ({"search": "accountaccount"}, ["AccountAccount1", "AccountAccount2"]),
        ({"search": "Account1"}, ["Account1", "AccountAccount1"]),
    ],
)
def test_apps_pagination_with_filtering(
    filter_by,
    apps_order,
    staff_api_client,
    apps_for_pagination,
    permission_manage_apps,
):
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(
        QUERY_APP_PAGINATION,
        variables,
    )
    content = get_graphql_content(response)

    nodes = content["data"]["apps"]["edges"]
    assert apps_order[0] == nodes[0]["node"]["name"]
    assert apps_order[1] == nodes[1]["node"]["name"]
    assert len(nodes) == page_size
