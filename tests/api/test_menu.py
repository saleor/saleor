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
    mutation mc($menu_name: String!){
        menuCreate(input: {name: $menu_name}) {
            menu {
                name
            }
        }
    }
    """
    variables = json.dumps({'menu_name': 'test-menu'})
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
