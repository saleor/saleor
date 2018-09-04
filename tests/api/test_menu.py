import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content

from saleor.graphql.menu.mutations import NavigationType

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
    variables = json.dumps({'menu_name': menu.name})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['menu']['name'] == menu.name

    # test query by id
    menu_id = graphene.Node.to_global_id('Menu', menu.id)
    variables = json.dumps({'id': menu_id})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['menu']['name'] == menu.name

    # test query by invalid name returns null
    variables = json.dumps({'menu_name': 'not-a-menu'})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert not content['data']['menu']


def test_menus_query(user_api_client, menu, menu_item):
    query = """
    query menus($menu_name: String){
        menus(query: $menu_name, first: 1) {
            edges {
                node {
                    name
                    items(first: 1) {
                        edges {
                            node {
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
        }
    }
    """

    menu.items.add(menu_item)
    menu.save()
    menu_name = menu.name
    variables = json.dumps({'menu_name': menu_name})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    menu_data = content['data']['menus']['edges'][0]['node']
    assert menu_data['name'] == menu.name
    items = menu_data['items']['edges'][0]['node']
    assert items['name'] == menu_item.name
    assert items['url'] == menu_item.url
    assert items['menu']['name'] == menu.name


def test_menu_items_query(user_api_client, menu_item, collection):
    query = """
    query menuitem($id: ID!) {
        menuItem(id: $id) {
            name
            children {
                totalCount
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
    variables = json.dumps(
        {'id': graphene.Node.to_global_id('MenuItem', menu_item.pk)})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['menuItem']
    assert data['name'] == menu_item.name
    assert data['children']['totalCount'] == menu_item.children.count()
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
    variables = json.dumps(
        {'id': graphene.Node.to_global_id('MenuItem', menu_item.pk)})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['menuItem']
    assert data['name'] == menu_item.name
    assert data['url'] == menu_item.url
    assert not data['category']
    assert not data['page']


def test_create_menu(admin_api_client, collection, category, page):
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
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
    }
    """

    category_id = graphene.Node.to_global_id('Category', category.pk)
    collection_id = graphene.Node.to_global_id('Collection', collection.pk)
    page_id = graphene.Node.to_global_id('Page', page.pk)
    url = 'http://www.example.com'

    variables = json.dumps({
        'name': 'test-menu', 'collection': collection_id,
        'category': category_id, 'page': page_id, 'url': url })
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['menuCreate']['menu']['name'] == 'test-menu'


def test_update_menu(admin_api_client, menu):
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
    variables = json.dumps({'id': menu_id, 'name': name})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['menuUpdate']['menu']['name'] == name

def test_delete_menu(admin_api_client, menu):
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
    variables = json.dumps({'id': menu_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['menuDelete']['menu']['name'] == menu.name
    with pytest.raises(menu._meta.model.DoesNotExist):
        menu.refresh_from_db()


def test_create_menu_item(admin_api_client, menu):
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
    variables = json.dumps({'name': name, 'url': url, 'menu_id': menu_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['menuItemCreate']['menuItem']
    assert data['name'] == name
    assert data['url'] == url
    assert data['menu']['name'] == menu.name


def test_update_menu_item(admin_api_client, menu, menu_item, page):
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
    variables = json.dumps({'id': menu_item_id, 'page': page_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['menuItemUpdate']['menuItem']
    assert data['page']['id'] == page_id


def test_delete_menu_item(admin_api_client, menu_item):
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
    variables = json.dumps({'id': menu_item_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['menuItemDelete']['menuItem']
    assert data['name'] == menu_item.name
    with pytest.raises(menu_item._meta.model.DoesNotExist):
        menu_item.refresh_from_db()


def test_add_more_than_one_item(admin_api_client, menu, menu_item, page):
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
    variables = json.dumps({'id': menu_item_id, 'page': page_id, 'url': url})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
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
    variables = json.dumps({
        'menu': menu_id, 'navigationType': NavigationType.MAIN.name})
    response = staff_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    staff_api_client.user.user_permissions.add(permission_manage_menus)
    staff_api_client.user.user_permissions.add(permission_manage_settings)

    # test assigning main menu
    response = staff_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['assignNavigation']['menu']['name'] == menu.name
    site_settings.refresh_from_db()
    assert site_settings.top_menu.name == menu.name

    # test assigning secondary menu
    variables = json.dumps({
        'menu': menu_id, 'navigationType': NavigationType.SECONDARY.name})
    response = staff_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['assignNavigation']['menu']['name'] == menu.name
    site_settings.refresh_from_db()
    assert site_settings.bottom_menu.name == menu.name

    # test unasigning menu
    variables = json.dumps({
        'id': None, 'navigationType': NavigationType.MAIN.name})
    response = staff_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert not content['data']['assignNavigation']['menu']
    site_settings.refresh_from_db()
    assert site_settings.top_menu is None
