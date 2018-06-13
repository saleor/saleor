import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content


def test_menu_query(user_api_client, menu, menu_item):
    query = """
    query menus($menu_name: String){
        menus(name: $menu_name) {
            edges {
                node {
                    name
                    items {
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
        }
    }
    """
    menu_item.collection = collection
    menu_item.save()
    variables = json.dumps(
        {'id': graphene.Node.to_global_id('MenuItem', menu_item.pk)})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['menuItem']
    assert data['name'] == menu_item.name
    assert data['collection']['name'] == menu_item.collection.name
    assert data['children']['totalCount'] == menu_item.children.count()


def test_create_menu(admin_api_client):
    query = """
    mutation mc($name: String!){
        menuCreate(input: {name: $name}) {
            menu {
                name
            }
        }
    }
    """
    variables = json.dumps({'name': 'test-menu'})
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
    mutation updateMenuItem($id: ID!, $menu_id: ID!, $page: ID) {
        menuItemUpdate(id: $id, input: {menu: $menu_id, page: $page}) {
            menuItem {
                url
                page {
                    title
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
    menu_id = graphene.Node.to_global_id('Menu', menu.pk)
    variables = json.dumps(
        {'id': menu_item_id, 'page': page_id, 'menu_id': menu_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['menuItemUpdate']['menuItem']
    assert not data['url']
    assert data['page']['title'] == page.title


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
