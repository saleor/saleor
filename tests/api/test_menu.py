import json

import graphene
import pytest
from django.core.exceptions import ValidationError

from saleor.graphql.menu.mutations import NavigationType, _validate_menu_item_instance
from saleor.menu.models import Menu, MenuItem
from saleor.product.models import Category
from tests.api.utils import get_graphql_content

from .utils import assert_no_permission, menu_item_to_json


def test_validate_menu_item_instance(category, page):
    _validate_menu_item_instance({"category": category}, "category", Category)
    with pytest.raises(ValidationError):
        _validate_menu_item_instance({"category": page}, "category", Category)

    # test that validation passes with empty values passed in input
    _validate_menu_item_instance({}, "category", Category)
    _validate_menu_item_instance({"category": None}, "category", Category)


def test_menu_query(user_api_client, menu):
    query = """
    query menu($id: ID, $menu_name: String){
        menu(id: $id, name: $menu_name) {
            name
        }
    }
    """

    # test query by name
    variables = {"menu_name": menu.name}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["menu"]["name"] == menu.name

    # test query by id
    menu_id = graphene.Node.to_global_id("Menu", menu.id)
    variables = {"id": menu_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["menu"]["name"] == menu.name

    # test query by invalid name returns null
    variables = {"menu_name": "not-a-menu"}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["menu"]


@pytest.mark.parametrize(
    "menu_filter, count", [({"search": "Menu1"}, 1), ({"search": "Menu"}, 2)]
)
def test_menus_query_with_filter(
    menu_filter, count, staff_api_client, permission_manage_menus
):
    query = """
        query ($filter: MenuFilterInput) {
            menus(first: 5, filter:$filter) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    Menu.objects.create(name="Menu1")
    Menu.objects.create(name="Menu2")
    variables = {"filter": menu_filter}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["menus"]["totalCount"] == count


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
    menu = Menu.objects.create(name="menu1")
    MenuItem.objects.create(name="MenuItem1", menu=menu)
    MenuItem.objects.create(name="MenuItem2", menu=menu)
    navbar = Menu.objects.get(name="navbar")
    MenuItem.objects.create(name="NavbarMenuItem", menu=navbar)
    variables = {"sort_by": menu_sort}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    response = staff_api_client.post_graphql(QUERY_MENU_WITH_SORT, variables)
    content = get_graphql_content(response)
    menus = content["data"]["menus"]["edges"]

    for order, menu_name in enumerate(result_order):
        assert menus[order]["node"]["name"] == menu_name


def test_menu_items_query(user_api_client, menu_item, collection):
    query = """
    query menuitem($id: ID!) {
        menuItem(id: $id) {
            name
            children {
                name
            }
            collection {
                name
            }
            category {
                id
            }
            page {
                id
            }
            url
        }
    }
    """
    menu_item.collection = collection
    menu_item.url = None
    menu_item.save()
    child_menu = MenuItem.objects.create(
        menu=menu_item.menu, name="Link 2", url="http://example2.com/", parent=menu_item
    )
    variables = {"id": graphene.Node.to_global_id("MenuItem", menu_item.pk)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["menuItem"]
    assert data["name"] == menu_item.name
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == child_menu.name
    assert data["collection"]["name"] == collection.name
    assert not data["category"]
    assert not data["page"]
    assert data["url"] is None


@pytest.mark.parametrize(
    "menu_item_filter, count",
    [({"search": "MenuItem1"}, 1), ({"search": "MenuItem"}, 2)],
)
def test_menu_items_query_with_filter(
    menu_item_filter, count, staff_api_client, permission_manage_menus
):
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
    menu = Menu.objects.create(name="Menu1")
    MenuItem.objects.create(name="MenuItem1", menu=menu)
    MenuItem.objects.create(name="MenuItem2", menu=menu)
    variables = {"filter": menu_item_filter}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["menuItems"]["totalCount"] == count


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
    menu = Menu.objects.create(name="Menu1")
    MenuItem.objects.create(name="MenuItem1", menu=menu)
    MenuItem.objects.create(name="MenuItem2", menu=menu)
    variables = {"sort_by": menu_item_sort}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    response = staff_api_client.post_graphql(QUERY_MENU_ITEMS_WITH_SORT, variables)
    content = get_graphql_content(response)
    menu_items = content["data"]["menuItems"]["edges"]

    for order, menu_item_name in enumerate(result_order):
        assert menu_items[order]["node"]["name"] == menu_item_name


def test_menu_item_query_static_url(user_api_client, menu_item):
    query = """
    query menuitem($id: ID!) {
        menuItem(id: $id) {
            name
            url
            category {
                id
            }
            page {
                id
            }
        }
    }
    """
    menu_item.url = "http://example.com"
    menu_item.save()
    variables = {"id": graphene.Node.to_global_id("MenuItem", menu_item.pk)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["menuItem"]
    assert data["name"] == menu_item.name
    assert data["url"] == menu_item.url
    assert not data["category"]
    assert not data["page"]


def test_create_menu(
    staff_api_client, collection, category, page, permission_manage_menus
):
    query = """
    mutation mc($name: String!, $collection: ID,
            $category: ID, $page: ID, $url: String) {

        menuCreate(input: {
            name: $name,
            items: [
                {name: "Collection item", collection: $collection},
                {name: "Page item", page: $page},
                {name: "Category item", category: $category},
                {name: "Url item", url: $url}]
        }) {
            menu {
                name
                items {
                    id
                }
            }
        }
    }
    """

    category_id = graphene.Node.to_global_id("Category", category.pk)
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    page_id = graphene.Node.to_global_id("Page", page.pk)
    url = "http://www.example.com"

    variables = {
        "name": "test-menu",
        "collection": collection_id,
        "category": category_id,
        "page": page_id,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    assert content["data"]["menuCreate"]["menu"]["name"] == "test-menu"


def test_update_menu(staff_api_client, menu, permission_manage_menus):
    query = """
    mutation updatemenu($id: ID!, $name: String!) {
        menuUpdate(id: $id, input: {name: $name}) {
            menu {
                name
            }
        }
    }
    """
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    name = "Blue oyster menu"
    variables = {"id": menu_id, "name": name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    assert content["data"]["menuUpdate"]["menu"]["name"] == name


def test_delete_menu(staff_api_client, menu, permission_manage_menus):
    query = """
        mutation deletemenu($id: ID!) {
            menuDelete(id: $id) {
                menu {
                    name
                }
            }
        }
        """
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"id": menu_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    assert content["data"]["menuDelete"]["menu"]["name"] == menu.name
    with pytest.raises(menu._meta.model.DoesNotExist):
        menu.refresh_from_db()


def test_create_menu_item(staff_api_client, menu, permission_manage_menus):
    query = """
    mutation createMenuItem($menu_id: ID!, $name: String!, $url: String){
        menuItemCreate(input: {name: $name, menu: $menu_id, url: $url}) {
            menuItem {
                name
                url
                menu {
                    name
                }
            }
        }
    }
    """
    name = "item menu"
    url = "http://www.example.com"
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"name": name, "url": url, "menu_id": menu_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    data = content["data"]["menuItemCreate"]["menuItem"]
    assert data["name"] == name
    assert data["url"] == url
    assert data["menu"]["name"] == menu.name

    menu.refresh_from_db()
    item = menu.items.get(name=name)
    item_json = menu_item_to_json(item)
    assert item_json in menu.json_content


def test_update_menu_item(
    staff_api_client, menu, menu_item, page, permission_manage_menus
):
    query = """
    mutation updateMenuItem($id: ID!, $page: ID) {
        menuItemUpdate(id: $id, input: {page: $page}) {
            menuItem {
                page {
                    id
                }
            }
        }
    }
    """
    # Menu item before update has url, but no page
    assert menu_item.url
    assert not menu_item.page
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    page_id = graphene.Node.to_global_id("Page", page.pk)
    variables = {"id": menu_item_id, "page": page_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    data = content["data"]["menuItemUpdate"]["menuItem"]
    assert data["page"]["id"] == page_id

    menu_item.refresh_from_db()
    menu.refresh_from_db()
    item_json = menu_item_to_json(menu_item)
    assert item_json in menu.json_content


def test_delete_menu_item(staff_api_client, menu_item, permission_manage_menus):
    query = """
        mutation deleteMenuItem($id: ID!) {
            menuItemDelete(id: $id) {
                menuItem {
                    name
                }
            }
        }
        """
    menu = menu_item.menu
    item_json = menu_item_to_json(menu_item)
    menu_json = menu.json_content
    assert item_json in menu_json

    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    variables = {"id": menu_item_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    data = content["data"]["menuItemDelete"]["menuItem"]
    assert data["name"] == menu_item.name
    with pytest.raises(menu_item._meta.model.DoesNotExist):
        menu_item.refresh_from_db()

    menu.refresh_from_db()
    assert item_json not in menu.json_content


def test_add_more_than_one_item(
    staff_api_client, menu, menu_item, page, permission_manage_menus
):
    query = """
    mutation updateMenuItem($id: ID!, $page: ID, $url: String) {
        menuItemUpdate(id: $id,
        input: {page: $page, url: $url}) {
        errors {
            field
            message
        }
            menuItem {
                url
            }
        }
    }
    """
    url = "http://www.example.com"
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    page_id = graphene.Node.to_global_id("Page", page.pk)
    variables = {"id": menu_item_id, "page": page_id, "url": url}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    data = content["data"]["menuItemUpdate"]["errors"][0]
    assert data["message"] == "More than one item provided."


def test_assign_menu(
    staff_api_client,
    menu,
    permission_manage_menus,
    permission_manage_settings,
    site_settings,
):
    query = """
    mutation AssignMenu($menu: ID, $navigationType: NavigationType!) {
        assignNavigation(menu: $menu, navigationType: $navigationType) {
            errors {
                field
                message
            }
            menu {
                name
            }
        }
    }
    """

    # test mutations fails without proper permissions
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"menu": menu_id, "navigationType": NavigationType.MAIN.name}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    staff_api_client.user.user_permissions.add(permission_manage_menus)
    staff_api_client.user.user_permissions.add(permission_manage_settings)

    # test assigning main menu
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["assignNavigation"]["menu"]["name"] == menu.name
    site_settings.refresh_from_db()
    assert site_settings.top_menu.name == menu.name

    # test assigning secondary menu
    variables = {"menu": menu_id, "navigationType": NavigationType.SECONDARY.name}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["assignNavigation"]["menu"]["name"] == menu.name
    site_settings.refresh_from_db()
    assert site_settings.bottom_menu.name == menu.name

    # test unasigning menu
    variables = {"id": None, "navigationType": NavigationType.MAIN.name}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["assignNavigation"]["menu"]
    site_settings.refresh_from_db()
    assert site_settings.top_menu is None


QUERY_REORDER_MENU = """
mutation menuItemMove($menu: ID!, $moves: [MenuItemMoveInput]!) {
  menuItemMove(menu: $menu, moves: $moves) {
    errors {
      field
      message
    }

    menu {
      id
      items {
        id
        parent {
          id
        }
        children {
          id
          parent {
            id
          }
          children {
            id
          }
        }
      }
    }
  }
}
"""


def test_menu_reorder(staff_api_client, permission_manage_menus, menu_item_list):

    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    assert len(menu_item_list) == 3

    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[0], "parentId": None, "sortOrder": 0},
        {"itemId": items_global_ids[1], "parentId": None, "sortOrder": -1},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": None},
    ]

    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": items_global_ids[1], "parent": None, "children": []},
            {"id": items_global_ids[0], "parent": None, "children": []},
            {"id": items_global_ids[2], "parent": None, "children": []},
        ],
    }

    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the order is right
    assert menu_data == expected_data


def test_menu_reorder_assign_parent(
    staff_api_client, permission_manage_menus, menu_item_list
):
    """Assign a menu item as parent of given menu items. Ensure the menu items
    are properly pushed at the bottom of the item's children.
    """

    menu_item_list = list(menu_item_list)
    assert len(menu_item_list) == 3

    menu_id = graphene.Node.to_global_id("Menu", menu_item_list[1].menu_id)

    root = menu_item_list[0]
    item0 = MenuItem.objects.create(menu=root.menu, parent=root, name="Default Link")
    menu_item_list.insert(0, item0)

    parent_global_id = graphene.Node.to_global_id("MenuItem", root.pk)
    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {
            "itemId": items_global_ids[2],
            "parentId": parent_global_id,
            "sortOrder": None,
        },
        {
            "itemId": items_global_ids[3],
            "parentId": parent_global_id,
            "sortOrder": None,
        },
    ]

    expected_data = {
        "id": menu_id,
        "items": [
            {
                "id": items_global_ids[1],
                "parent": None,
                "children": [
                    {
                        "id": items_global_ids[0],
                        "parent": {"id": parent_global_id},
                        "children": [],
                    },
                    {
                        "id": items_global_ids[2],
                        "parent": {"id": parent_global_id},
                        "children": [],
                    },
                    {
                        "id": items_global_ids[3],
                        "parent": {"id": parent_global_id},
                        "children": [],
                    },
                ],
            }
        ],
    }

    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the parent and sort orders were assigned correctly
    assert menu_data == expected_data


def test_menu_reorder_assign_parent_to_top_level(
    staff_api_client, permission_manage_menus, menu_item_list
):
    """Set the parent of an item to None, to put it as to the root level."""

    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    unchanged_item_global_id = graphene.Node.to_global_id(
        "MenuItem", menu_item_list[2].pk
    )

    root_candidate = menu_item_list[0]
    root_candidate_global_id = graphene.Node.to_global_id("MenuItem", root_candidate.pk)

    # Give to the item menu a parent
    previous_parent = menu_item_list[1]
    previous_parent_global_id = graphene.Node.to_global_id(
        "MenuItem", previous_parent.pk
    )
    root_candidate.move_to(previous_parent)
    root_candidate.save()

    assert root_candidate.parent

    moves_input = [
        {"itemId": root_candidate_global_id, "parentId": None, "sortOrder": None}
    ]
    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": previous_parent_global_id, "parent": None, "children": []},
            {"id": unchanged_item_global_id, "parent": None, "children": []},
            {"id": root_candidate_global_id, "parent": None, "children": []},
        ],
    }

    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the the item was successfully placed at the root
    # and is now at the bottom of the list (default)
    assert menu_data == expected_data


def test_menu_reorder_cannot_assign_to_ancestor(
    staff_api_client, permission_manage_menus, menu_item_list
):

    menu_item_list = list(menu_item_list)
    menu_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    root = menu_item_list[0]
    root_node_id = graphene.Node.to_global_id("MenuItem", root.pk)

    child = menu_item_list[2]
    child_node_id = graphene.Node.to_global_id("MenuItem", child.pk)

    # Give the child an ancestor
    child.move_to(root)
    child.save()

    # Give the child an ancestor
    child.move_to(root)
    child.save()

    assert not root.parent
    assert child.parent

    moves = [{"itemId": root_node_id, "parentId": child_node_id, "sortOrder": None}]

    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves, "menu": menu_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    assert response["errors"] == [
        {
            "field": "parentId",
            "message": "Cannot assign a node as child of " "one of its descendants.",
        }
    ]


def test_menu_reorder_cannot_assign_to_itself(
    staff_api_client, permission_manage_menus, menu_item
):

    menu_id = graphene.Node.to_global_id("Menu", menu_item.menu_id)
    node_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    moves = [{"itemId": node_id, "parentId": node_id, "sortOrder": None}]

    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves, "menu": menu_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    assert response["errors"] == [
        {"field": "parentId", "message": "Cannot assign a node to itself."}
    ]


def test_menu_cannot_get_menu_item_not_from_same_menu(
    staff_api_client, permission_manage_menus, menu_item
):
    """You shouldn't be able to edit menu items that are not from the menu
    you are actually editing"""

    menu_without_items = Menu.objects.create(name="this menu has no items")

    menu_id = graphene.Node.to_global_id("Menu", menu_without_items.id)
    node_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    moves = [{"itemId": node_id}]

    response = staff_api_client.post_graphql(
        QUERY_REORDER_MENU, {"moves": moves, "menu": menu_id}, [permission_manage_menus]
    )

    assert json.loads(response.content) == {
        "data": {
            "menuItemMove": {
                "errors": [
                    {
                        "field": "item",
                        "message": f"Couldn't resolve to a node: {node_id}",
                    }
                ],
                "menu": None,
            }
        }
    }


def test_menu_cannot_pass_an_invalid_menu_item_node_type(
    staff_api_client, staff_user, permission_manage_menus, menu_item
):
    """You shouldn't be able to pass a menu item node
    that is not an actual MenuType."""

    menu_without_items = Menu.objects.create(name="this menu has no items")

    menu_id = graphene.Node.to_global_id("Menu", menu_without_items.id)
    node_id = graphene.Node.to_global_id("User", staff_user.pk)
    moves = [{"itemId": node_id}]

    response = staff_api_client.post_graphql(
        QUERY_REORDER_MENU, {"moves": moves, "menu": menu_id}, [permission_manage_menus]
    )

    assert json.loads(response.content) == {
        "data": {
            "menuItemMove": {
                "errors": [{"field": "item", "message": f"Must receive a MenuItem id"}],
                "menu": None,
            }
        }
    }
