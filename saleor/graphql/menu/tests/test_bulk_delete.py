import graphene
import pytest

from saleor.menu.models import Menu, MenuItem
from tests.api.utils import get_graphql_content, menu_item_to_json


@pytest.fixture
def menu_list():
    menu_1 = Menu.objects.create(name="test-navbar-1", json_content={})
    menu_2 = Menu.objects.create(name="test-navbar-2", json_content={})
    menu_3 = Menu.objects.create(name="test-navbar-3", json_content={})
    return menu_1, menu_2, menu_3


def test_delete_menus(staff_api_client, menu_list, permission_manage_menus):
    query = """
    mutation menuBulkDelete($ids: [ID]!) {
        menuBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Menu", collection.id)
            for collection in menu_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    assert content["data"]["menuBulkDelete"]["count"] == 3
    assert not Menu.objects.filter(id__in=[menu.id for menu in menu_list]).exists()


def test_delete_menu_items(staff_api_client, menu_item_list, permission_manage_menus):
    query = """
    mutation menuItemBulkDelete($ids: [ID]!) {
        menuItemBulkDelete(ids: $ids) {
            count
        }
    }
    """
    menu = menu_item_list[0].menu
    items_json = [menu_item_to_json(item) for item in menu_item_list]

    variables = {
        "ids": [
            graphene.Node.to_global_id("MenuItem", menu_item.id)
            for menu_item in menu_item_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    assert content["data"]["menuItemBulkDelete"]["count"] == len(menu_item_list)
    assert not MenuItem.objects.filter(
        id__in=[menu_item.id for menu_item in menu_item_list]
    ).exists()

    menu.refresh_from_db()
    for item_json in items_json:
        assert item_json not in menu.json_content


def test_delete_empty_list_of_ids(staff_api_client, permission_manage_menus):
    query = """
    mutation menuItemBulkDelete($ids: [ID]!) {
        menuItemBulkDelete(ids: $ids) {
            count
        }
    }
    """
    menu_item_list = []
    variables = {"ids": menu_item_list}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    assert content["data"]["menuItemBulkDelete"]["count"] == len(menu_item_list)
