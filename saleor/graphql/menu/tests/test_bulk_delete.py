import graphene
import pytest

from ....menu.models import Menu, MenuItem
from ...tests.utils import get_graphql_content


@pytest.fixture
def menu_list():
    menu_1 = Menu.objects.create(name="test-navbar-1", slug="test-navbar-1")
    menu_2 = Menu.objects.create(name="test-navbar-2", slug="test-navbar-2")
    menu_3 = Menu.objects.create(name="test-navbar-3", slug="test-navbar-3")
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
