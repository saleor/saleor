import json
from random import shuffle
from typing import Dict, List

import graphene
import pytest
from graphql_relay import from_global_id

from saleor.graphql.menu.mutations import NavigationType
from saleor.menu.models import MenuItem, Menu
from tests.api.utils import get_graphql_content

from .utils import assert_no_permission


def test_menu_query(user_api_client, menu):
    query = """
    query menu($id: ID, $menu_name: String){
        menu(id: $id, name: $menu_name) {
            name
        }
    }
    """

    # test query by name
    variables = {'menu_name': menu.name}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content['data']['menu']['name'] == menu.name

    # test query by id
    menu_id = graphene.Node.to_global_id('Menu', menu.id)
    variables = {'id': menu_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content['data']['menu']['name'] == menu.name

    # test query by invalid name returns null
    variables = {'menu_name': 'not-a-menu'}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content['data']['menu']


def test_menus_query(user_api_client, menu, menu_item):
    query = """
    query menus($menu_name: String){
        menus(query: $menu_name, first: 1) {
            edges {
                node {
                    name
                    items {
                        name
                        menu {
                            name
                        }
                        url
                    }
                }
            }
        }
    }
    """

    menu.items.add(menu_item)
    menu.save()
    menu_name = menu.name
    variables = {'menu_name': menu_name}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    menu_data = content['data']['menus']['edges'][0]['node']
    assert menu_data['name'] == menu.name
    items = menu_data['items']
    assert len(items) == 1
    item = items[0]
    assert item['name'] == menu_item.name
    assert item['url'] == menu_item.url
    assert item['menu']['name'] == menu.name


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
        menu=menu_item.menu, name='Link 2', url='http://example2.com/',
        parent=menu_item)
    variables = {'id': graphene.Node.to_global_id('MenuItem', menu_item.pk)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['menuItem']
    assert data['name'] == menu_item.name
    assert len(data['children']) == 1
    assert data['children'][0]['name'] == child_menu.name
    assert data['collection']['name'] == collection.name
    assert not data['category']
    assert not data['page']
    assert data['url'] is None


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
    variables = {'id': graphene.Node.to_global_id('MenuItem', menu_item.pk)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['menuItem']
    assert data['name'] == menu_item.name
    assert data['url'] == menu_item.url
    assert not data['category']
    assert not data['page']


def test_create_menu(
        staff_api_client, collection, category, page, permission_manage_menus):
    query = """
    mutation mc($name: String!, $collection: ID, $category: ID, $page: ID, $url: String) {
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

    category_id = graphene.Node.to_global_id('Category', category.pk)
    collection_id = graphene.Node.to_global_id('Collection', collection.pk)
    page_id = graphene.Node.to_global_id('Page', page.pk)
    url = 'http://www.example.com'

    variables = {
        'name': 'test-menu', 'collection': collection_id,
        'category': category_id, 'page': page_id, 'url': url}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)
    assert content['data']['menuCreate']['menu']['name'] == 'test-menu'


def test_update_menu(
        staff_api_client, menu, permission_manage_menus):
    query = """
    mutation updatemenu($id: ID!, $name: String!) {
        menuUpdate(id: $id, input: {name: $name}) {
            menu {
                name
            }
        }
    }
    """
    menu_id = graphene.Node.to_global_id('Menu', menu.pk)
    name = 'Blue oyster menu'
    variables = {'id': menu_id, 'name': name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)
    assert content['data']['menuUpdate']['menu']['name'] == name


def test_delete_menu(
        staff_api_client, menu, permission_manage_menus):
    query = """
        mutation deletemenu($id: ID!) {
            menuDelete(id: $id) {
                menu {
                    name
                }
            }
        }
        """
    menu_id = graphene.Node.to_global_id('Menu', menu.pk)
    variables = {'id': menu_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)
    assert content['data']['menuDelete']['menu']['name'] == menu.name
    with pytest.raises(menu._meta.model.DoesNotExist):
        menu.refresh_from_db()


def test_create_menu_item(
        staff_api_client, menu, permission_manage_menus):
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
    name = 'item menu'
    url = 'http://www.example.com'
    menu_id = graphene.Node.to_global_id('Menu', menu.pk)
    variables = {'name': name, 'url': url, 'menu_id': menu_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)
    data = content['data']['menuItemCreate']['menuItem']
    assert data['name'] == name
    assert data['url'] == url
    assert data['menu']['name'] == menu.name


def test_update_menu_item(
        staff_api_client, menu, menu_item, page, permission_manage_menus):
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
    menu_item_id = graphene.Node.to_global_id('MenuItem', menu_item.pk)
    page_id = graphene.Node.to_global_id('Page', page.pk)
    variables = {'id': menu_item_id, 'page': page_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)
    data = content['data']['menuItemUpdate']['menuItem']
    assert data['page']['id'] == page_id


def test_delete_menu_item(
        staff_api_client, menu_item, permission_manage_menus):
    query = """
        mutation deleteMenuItem($id: ID!) {
            menuItemDelete(id: $id) {
                menuItem {
                    name
                }
            }
        }
        """
    menu_item_id = graphene.Node.to_global_id('MenuItem', menu_item.pk)
    variables = {'id': menu_item_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)
    data = content['data']['menuItemDelete']['menuItem']
    assert data['name'] == menu_item.name
    with pytest.raises(menu_item._meta.model.DoesNotExist):
        menu_item.refresh_from_db()


def test_add_more_than_one_item(
        staff_api_client, menu, menu_item, page, permission_manage_menus):
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
    url = 'http://www.example.com'
    menu_item_id = graphene.Node.to_global_id('MenuItem', menu_item.pk)
    page_id = graphene.Node.to_global_id('Page', page.pk)
    variables = {'id': menu_item_id, 'page': page_id, 'url': url}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)
    data = content['data']['menuItemUpdate']['errors'][0]
    assert data['field'] == 'items'
    assert data['message'] == 'More than one item provided.'


def test_assign_menu(
        staff_api_client, menu, permission_manage_menus,
        permission_manage_settings, site_settings):
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
    menu_id = graphene.Node.to_global_id('Menu', menu.pk)
    variables = {'menu': menu_id, 'navigationType': NavigationType.MAIN.name}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    staff_api_client.user.user_permissions.add(permission_manage_menus)
    staff_api_client.user.user_permissions.add(permission_manage_settings)

    # test assigning main menu
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content['data']['assignNavigation']['menu']['name'] == menu.name
    site_settings.refresh_from_db()
    assert site_settings.top_menu.name == menu.name

    # test assigning secondary menu
    variables = {
        'menu': menu_id, 'navigationType': NavigationType.SECONDARY.name}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content['data']['assignNavigation']['menu']['name'] == menu.name
    site_settings.refresh_from_db()
    assert site_settings.bottom_menu.name == menu.name

    # test unasigning menu
    variables = {'id': None, 'navigationType': NavigationType.MAIN.name}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content['data']['assignNavigation']['menu']
    site_settings.refresh_from_db()
    assert site_settings.top_menu is None


QUERY_REORDER_MENU = '''
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
        sortOrder
        parent {
          id
        }
        children {
          id
          sortOrder
          parent {
            id
          }
        }
      }
    }
  }
}
'''


def _assert_menu_is_exactly(
        menu_id: str,
        actual_data: dict, expected_data: List[Dict]):

    menu = actual_data.get('menu')
    assert menu, 'Expected to receive a valid menu to compare from'

    # Check the returned menu is actually the one we requested to change
    assert menu['id'] == menu_id

    actual_menu_items = menu.get('items')
    assert actual_menu_items, 'Expected the menu to have items'

    for expected_item in expected_data:
        the_item_was_found = False
        expected_sort_order = expected_item.get('sortOrder')
        expected_parent_id = expected_item.get('parentId')
        expected_item_id = from_global_id(expected_item['itemId'])[1]

        for actual_item in actual_menu_items:
            # Get the item that we want to compare, we retrieve by the database
            # entry ID as the node id may have changed between the initial
            # request and the one returned by the mutation
            actual_item_id = from_global_id(actual_item['id'])[1]
            if actual_item_id != expected_item_id:
                # Append the children, to check, if any
                children = actual_item.get('children')
                if children:
                    actual_menu_items += children

                # Skip this node as it is not the one we are looking for
                continue

            the_item_was_found = True

            if expected_sort_order:
                assert actual_item['sortOrder'] == expected_sort_order, \
                    'The menu item did not have the expected sorting order'

            if 'parentId' in expected_item:
                if expected_parent_id:
                    assert actual_item['parent'], \
                        'Expected the menu item to have a parent'
                    assert actual_item['parent']['id'] == expected_parent_id, \
                        'The menu item did not have the expected parent'
                else:
                    assert not actual_item['parent'], \
                        'Expected the menu item to not have a parent'

        assert the_item_was_found, \
            'The expected menu item was not found in the response'


def test_menu_reorder(
        staff_api_client, permission_manage_menus, menu_item_list):

    menu_item_list = list(menu_item_list)
    menu_id = graphene.Node.to_global_id('Menu', menu_item_list[0].menu_id)

    # Randomize the menu ordering
    shuffle(menu_item_list)

    moves = [{
        "itemId": graphene.Node.to_global_id('MenuItem', item.pk),
        "parentId": None, "sortOrder": pos
    } for pos, item in enumerate(menu_item_list)]

    response = get_graphql_content(staff_api_client.post_graphql(
        QUERY_REORDER_MENU,
        {
            'moves': moves,
            'menu': menu_id
        },
        [permission_manage_menus])
    )['data']['menuItemMove']
    assert not response.get('errors')

    # Ensure the order is right
    _assert_menu_is_exactly(menu_id, response, moves)


def test_menu_reorder_assign_parent(
        staff_api_client, permission_manage_menus, menu_item_list):

    menu_item_list = list(menu_item_list)
    menu_id = graphene.Node.to_global_id('Menu', menu_item_list[1].menu_id)

    root = menu_item_list[0]
    moves = [{
        "itemId": graphene.Node.to_global_id('MenuItem', item.pk),
        "parentId": graphene.Node.to_global_id('MenuItem', root.pk),
        "sortOrder": None
    } for item in menu_item_list[1:]]

    response = get_graphql_content(staff_api_client.post_graphql(
        QUERY_REORDER_MENU,
        {
            'moves': moves,
            'menu': menu_id
        },
        [permission_manage_menus]
    ))['data']['menuItemMove']
    assert not response.get('errors')

    # Ensure the parent were assigned correctly
    _assert_menu_is_exactly(menu_id, response, moves)


def test_menu_reorder_assign_parent_to_top_level(
        staff_api_client, permission_manage_menus, menu_item_list):

    menu_item_list = list(menu_item_list)
    menu_id = graphene.Node.to_global_id('Menu', menu_item_list[0].menu_id)

    root = menu_item_list[0]
    root_node_id = graphene.Node.to_global_id('MenuItem', root.pk)

    # Give to the item menu a parent
    root.move_to(menu_item_list[1])
    root.save()

    assert root.parent

    moves = [{
        "itemId": root_node_id,
        "parentId": None,
        "sortOrder": None
    }]

    response = get_graphql_content(staff_api_client.post_graphql(
        QUERY_REORDER_MENU,
        {
            'moves': moves,
            'menu': menu_id
        },
        [permission_manage_menus]
    ))['data']['menuItemMove']
    assert not response.get('errors')

    # Ensure the order is right
    _assert_menu_is_exactly(menu_id, response, moves)


def test_menu_reorder_cannot_assign_to_ancestor(
        staff_api_client, permission_manage_menus, menu_item_list):

    menu_item_list = list(menu_item_list)
    menu_id = graphene.Node.to_global_id('Menu', menu_item_list[0].menu_id)

    root = menu_item_list[0]
    root_node_id = graphene.Node.to_global_id('MenuItem', root.pk)

    child = menu_item_list[2]
    child_node_id = graphene.Node.to_global_id('MenuItem', child.pk)

    # Give the child an ancestor
    child.move_to(root)
    child.save()

    # Give the child an ancestor
    child.move_to(root)
    child.save()

    assert not root.parent
    assert child.parent

    moves = [{
        "itemId": root_node_id,
        "parentId": child_node_id,
        "sortOrder": None
    }]

    response = get_graphql_content(staff_api_client.post_graphql(
        QUERY_REORDER_MENU,
        {
            'moves': moves,
            'menu': menu_id
        },
        [permission_manage_menus]
    ))['data']['menuItemMove']

    assert response['errors'] == [
        {'field': 'parent',
         'message': 'Cannot assign a node as child of '
                    'one of its descendants.'}]


def test_menu_reorder_cannot_assign_to_itself(
        staff_api_client, permission_manage_menus, menu_item):

    menu_id = graphene.Node.to_global_id('Menu', menu_item.menu_id)
    node_id = graphene.Node.to_global_id('MenuItem', menu_item.pk)
    moves = [{
        "itemId": node_id,
        "parentId": node_id,
        "sortOrder": None
    }]

    response = get_graphql_content(staff_api_client.post_graphql(
        QUERY_REORDER_MENU,
        {
            'moves': moves,
            'menu': menu_id
        },
        [permission_manage_menus]
    ))['data']['menuItemMove']

    assert response['errors'] == [
        {'field': 'parent',
         'message': 'Cannot assign a node to itself.'}]


def test_menu_cannot_get_menu_item_not_from_same_menu(
        staff_api_client, permission_manage_menus, menu_item):
    """You shouldn't be able to edit menu items that are not from the menu
    you are actually editing"""

    menu_without_items = Menu.objects.create(name='this menu has no items')

    menu_id = graphene.Node.to_global_id('Menu', menu_without_items.id)
    node_id = graphene.Node.to_global_id('MenuItem', menu_item.pk)
    moves = [{
        "itemId": node_id
    }]

    response = staff_api_client.post_graphql(
        QUERY_REORDER_MENU,
        {
            'moves': moves,
            'menu': menu_id
        },
        [permission_manage_menus]
    )

    assert (
        json.loads(
            response.content.decode('utf8'))['errors'][0]['message'] == (
                'MenuItem matching query does not exist.'))


def test_menu_cannot_pass_an_invalid_menu_item_node_type(
        staff_api_client, staff_user, permission_manage_menus, menu_item):
    """You shouldn't be able to pass a menu item node
    that is not an actual MenuType."""

    menu_without_items = Menu.objects.create(name='this menu has no items')

    menu_id = graphene.Node.to_global_id('Menu', menu_without_items.id)
    node_id = graphene.Node.to_global_id('User', staff_user.pk)
    moves = [{
        "itemId": node_id
    }]

    response = staff_api_client.post_graphql(
        QUERY_REORDER_MENU,
        {
            'moves': moves,
            'menu': menu_id
        },
        [permission_manage_menus]
    )

    assert (
        json.loads(
            response.content.decode('utf8'))['errors'][0]['message'] == (
                'The menu item node must be of type MenuItem.'))
