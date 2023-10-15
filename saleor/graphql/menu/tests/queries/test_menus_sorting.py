import pytest

from .....menu.models import Menu, MenuItem
from ....tests.utils import get_graphql_content

QUERY_MENU_WITH_SORT = """
    query ($sort_by: MenuSortingInput!) {
        menus(first:5, sortBy: $sort_by) {
            edges{
                node{
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "menu_sort, result_order",
    [
        # We have "footer" and "navbar" from default saleor configuration
        ({"field": "NAME", "direction": "ASC"}, ["footer", "menu1", "navbar"]),
        ({"field": "NAME", "direction": "DESC"}, ["navbar", "menu1", "footer"]),
        ({"field": "ITEMS_COUNT", "direction": "ASC"}, ["footer", "navbar", "menu1"]),
        ({"field": "ITEMS_COUNT", "direction": "DESC"}, ["menu1", "navbar", "footer"]),
    ],
)
def test_query_menus_with_sort(
    menu_sort, result_order, staff_api_client, permission_manage_menus
):
    # given
    menu = Menu.objects.create(name="menu1", slug="menu1")
    MenuItem.objects.create(name="MenuItem1", menu=menu)
    MenuItem.objects.create(name="MenuItem2", menu=menu)
    navbar = Menu.objects.get(name="navbar")
    MenuItem.objects.create(name="NavbarMenuItem", menu=navbar)
    variables = {"sort_by": menu_sort}
    staff_api_client.user.user_permissions.add(permission_manage_menus)

    # when
    response = staff_api_client.post_graphql(QUERY_MENU_WITH_SORT, variables)

    # then
    content = get_graphql_content(response)
    menus = content["data"]["menus"]["edges"]

    for order, menu_name in enumerate(result_order):
        assert menus[order]["node"]["name"] == menu_name


QUERY_MENU_ITEMS_WITH_SORT = """
    query ($sort_by: MenuItemSortingInput!) {
        menuItems(first:5, sortBy: $sort_by) {
            edges{
                node{
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "menu_item_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["MenuItem1", "MenuItem2"]),
        ({"field": "NAME", "direction": "DESC"}, ["MenuItem2", "MenuItem1"]),
    ],
)
def test_query_menu_items_with_sort(
    menu_item_sort, result_order, staff_api_client, permission_manage_menus
):
    # given
    menu = Menu.objects.create(name="Menu1", slug="Menu1")
    MenuItem.objects.create(name="MenuItem1", menu=menu)
    MenuItem.objects.create(name="MenuItem2", menu=menu)
    variables = {"sort_by": menu_item_sort}
    staff_api_client.user.user_permissions.add(permission_manage_menus)

    # when
    response = staff_api_client.post_graphql(QUERY_MENU_ITEMS_WITH_SORT, variables)

    # then
    content = get_graphql_content(response)
    menu_items = content["data"]["menuItems"]["edges"]

    for order, menu_item_name in enumerate(result_order):
        assert menu_items[order]["node"]["name"] == menu_item_name
