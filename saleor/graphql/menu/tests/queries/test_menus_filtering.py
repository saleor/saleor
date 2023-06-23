import pytest

from .....menu.models import Menu, MenuItem
from ....tests.utils import get_graphql_content

QUERY_MENU_WITH_FILTER = """
    query ($filter: MenuFilterInput) {
        menus(first: 5, filter:$filter) {
            totalCount
            edges {
                node {
                    id
                    name
                    slug
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "menu_filter, count",
    [
        ({"search": "Menu1"}, 1),
        ({"search": "Menu"}, 2),
        ({"slugs": ["Menu1", "Menu2"]}, 2),
        ({"slugs": []}, 4),
    ],
)
def test_menus_query_with_filter(
    menu_filter, count, staff_api_client, permission_manage_menus
):
    # given
    Menu.objects.create(name="Menu1", slug="Menu1")
    Menu.objects.create(name="Menu2", slug="Menu2")
    variables = {"filter": menu_filter}
    staff_api_client.user.user_permissions.add(permission_manage_menus)

    # when
    response = staff_api_client.post_graphql(QUERY_MENU_WITH_FILTER, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["menus"]["totalCount"] == count


def test_menus_query_with_slug_filter(staff_api_client, permission_manage_menus):
    # given
    Menu.objects.create(name="Menu1", slug="Menu1")
    Menu.objects.create(name="Menu2", slug="Menu2")
    Menu.objects.create(name="Menu3", slug="menu3-slug")
    variables = {"filter": {"search": "menu3-slug"}}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    # when
    response = staff_api_client.post_graphql(QUERY_MENU_WITH_FILTER, variables)

    # then
    content = get_graphql_content(response)
    menus = content["data"]["menus"]["edges"]
    assert len(menus) == 1
    assert menus[0]["node"]["slug"] == "menu3-slug"


def test_menus_query_with_slug_list_filter(staff_api_client, permission_manage_menus):
    # given
    Menu.objects.create(name="Menu1", slug="Menu1")
    Menu.objects.create(name="Menu2", slug="Menu2")
    Menu.objects.create(name="Menu3", slug="Menu3")
    variables = {"filter": {"slug": ["Menu2", "Menu3"]}}
    staff_api_client.user.user_permissions.add(permission_manage_menus)

    # when
    response = staff_api_client.post_graphql(QUERY_MENU_WITH_FILTER, variables)

    # then
    content = get_graphql_content(response)
    menus = content["data"]["menus"]["edges"]
    slugs = [node["node"]["slug"] for node in menus]
    assert len(menus) == 2
    assert "Menu2" in slugs
    assert "Menu3" in slugs


@pytest.mark.parametrize(
    "menu_item_filter, count",
    [({"search": "MenuItem1"}, 1), ({"search": "MenuItem"}, 2)],
)
def test_menu_items_query_with_filter(
    menu_item_filter, count, staff_api_client, permission_manage_menus
):
    # given
    query = """
        query ($filter: MenuItemFilterInput) {
            menuItems(first: 5, filter:$filter) {
                totalCount
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    """
    menu = Menu.objects.create(name="Menu1", slug="Menu1")
    MenuItem.objects.create(name="MenuItem1", menu=menu)
    MenuItem.objects.create(name="MenuItem2", menu=menu)
    variables = {"filter": menu_item_filter}
    staff_api_client.user.user_permissions.add(permission_manage_menus)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["menuItems"]["totalCount"] == count
