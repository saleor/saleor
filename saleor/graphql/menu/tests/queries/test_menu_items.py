import pytest

from .....menu.models import Menu, MenuItem
from ....tests.utils import get_graphql_content


@pytest.fixture
def menu_items_for_pagination(db):
    menu = Menu.objects.get(name="navbar")
    items = MenuItem.tree.build_tree_nodes(
        {
            "name": "Item1",
            "menu": menu,
            "children": [
                {"name": "ItemItem1", "menu": menu},
                {"name": "ItemItem2", "menu": menu},
                {"name": "Item2", "menu": menu},
                {"name": "Item3", "menu": menu},
            ],
        }
    )
    return MenuItem.objects.bulk_create(items)


QUERY_MENU_ITEMS_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: MenuItemSortingInput, $filter: MenuItemFilterInput
    ){
        menuItems(
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
    "sort_by, menu_items_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Item1", "Item2", "Item3"]),
        ({"field": "NAME", "direction": "DESC"}, ["ItemItem2", "ItemItem1", "Item3"]),
    ],
)
def test_menu_items_pagination_with_sorting(
    sort_by,
    menu_items_order,
    staff_api_client,
    menu_items_for_pagination,
):
    # given
    page_size = 3

    variables = {"first": page_size, "after": None, "sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_MENU_ITEMS_PAGINATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    menu_items_nodes = content["data"]["menuItems"]["edges"]
    assert menu_items_order[0] == menu_items_nodes[0]["node"]["name"]
    assert menu_items_order[1] == menu_items_nodes[1]["node"]["name"]
    assert menu_items_order[2] == menu_items_nodes[2]["node"]["name"]
    assert len(menu_items_nodes) == page_size


@pytest.mark.parametrize(
    "filter_by, menu_items_order",
    [
        ({"search": "ItemItem"}, ["ItemItem1", "ItemItem2"]),
        ({"search": "Item1"}, ["Item1", "ItemItem1"]),
    ],
)
def test_menu_items_pagination_with_filtering(
    filter_by,
    menu_items_order,
    staff_api_client,
    menu_items_for_pagination,
):
    # given
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_MENU_ITEMS_PAGINATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    menu_items_nodes = content["data"]["menuItems"]["edges"]
    assert menu_items_order[0] == menu_items_nodes[0]["node"]["name"]
    assert menu_items_order[1] == menu_items_nodes[1]["node"]["name"]
    assert len(menu_items_nodes) == page_size
