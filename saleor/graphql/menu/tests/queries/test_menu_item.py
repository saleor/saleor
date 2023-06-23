import graphene

from .....menu.models import MenuItem
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

QUERY_MENU_ITEM_BY_ID = """
query menuitem($id: ID!, $channel: String) {
    menuItem(id: $id, channel: $channel) {
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


def test_menu_item_query(user_api_client, menu_item, published_collection, channel_USD):
    query = QUERY_MENU_ITEM_BY_ID
    menu_item.collection = published_collection
    menu_item.url = None
    menu_item.save()
    child_menu = MenuItem.objects.create(
        menu=menu_item.menu, name="Link 2", url="http://example2.com/", parent=menu_item
    )
    variables = {
        "id": graphene.Node.to_global_id("MenuItem", menu_item.pk),
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["menuItem"]
    assert data["name"] == menu_item.name
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == child_menu.name
    assert data["collection"]["name"] == published_collection.name
    assert not data["category"]
    assert not data["page"]
    assert data["url"] is None


def test_menu_item_query_with_invalid_channel(
    user_api_client, menu_item, published_collection, channel_USD
):
    query = QUERY_MENU_ITEM_BY_ID
    menu_item.collection = published_collection
    menu_item.url = None
    menu_item.save()
    child_menu = MenuItem.objects.create(
        menu=menu_item.menu, name="Link 2", url="http://example2.com/", parent=menu_item
    )
    variables = {
        "id": graphene.Node.to_global_id("MenuItem", menu_item.pk),
        "channel": "invalid",
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["menuItem"]
    assert data["name"] == menu_item.name
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == child_menu.name
    assert not data["collection"]
    assert not data["category"]
    assert not data["page"]
    assert data["url"] is None


def test_staff_query_menu_item_by_invalid_id(staff_api_client, menu_item):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_MENU_ITEM_BY_ID, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["menuItem"] is None


def test_staff_query_menu_item_with_invalid_object_type(staff_api_client, menu_item):
    variables = {"id": graphene.Node.to_global_id("Order", menu_item.pk)}
    response = staff_api_client.post_graphql(QUERY_MENU_ITEM_BY_ID, variables)
    content = get_graphql_content(response)
    assert content["data"]["menuItem"] is None


def test_menu_items_collection_in_other_channel(
    user_api_client, menu_item, published_collection, channel_PLN
):
    query = """
    query menuitem($id: ID!, $channel: String) {
        menuItem(id: $id, channel: $channel) {
            name
            children {
                name
            }
            collection {
                name
            }
            menu {
                slug
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
    menu_item.collection = published_collection
    menu_item.url = None
    menu_item.save()
    child_menu = MenuItem.objects.create(
        menu=menu_item.menu, name="Link 2", url="http://example2.com/", parent=menu_item
    )
    variables = {
        "id": graphene.Node.to_global_id("MenuItem", menu_item.pk),
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["menuItem"]
    assert data["name"] == menu_item.name
    assert data["menu"]["slug"] == menu_item.menu.slug
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == child_menu.name
    assert not data["collection"]
    assert not data["category"]
    assert not data["page"]
    assert data["url"] is None


QUERY_MENU_ITEM = """
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


def test_menu_item_query_static_url(user_api_client, menu_item):
    # given
    query = QUERY_MENU_ITEM
    menu_item.url = "http://example.com"
    menu_item.save()
    variables = {"id": graphene.Node.to_global_id("MenuItem", menu_item.pk)}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["menuItem"]
    assert data["name"] == menu_item.name
    assert data["url"] == menu_item.url
    assert not data["category"]
    assert not data["page"]


def test_menu_item_query_staff_with_permission_gets_all_pages(
    staff_api_client, permission_manage_pages, menu_item, page
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    variables = {"id": graphene.Node.to_global_id("MenuItem", menu_item.pk)}

    page.is_published = False
    page.save(update_fields=["is_published"])

    menu_item.page = page
    menu_item.save(update_fields=["page"])

    # when
    response = staff_api_client.post_graphql(QUERY_MENU_ITEM, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["menuItem"]

    assert data["name"] == menu_item.name
    assert data["url"] == menu_item.url
    assert data["page"]["id"] == graphene.Node.to_global_id("Page", page.id)


def test_menu_item_query_staff_without_permission_gets_only_published_pages(
    staff_api_client, permission_manage_pages, menu_item, page
):
    # given
    variables = {"id": graphene.Node.to_global_id("MenuItem", menu_item.pk)}

    page.is_published = False
    page.save(update_fields=["is_published"])

    menu_item.page = page
    menu_item.save(update_fields=["page"])

    # when
    response = staff_api_client.post_graphql(QUERY_MENU_ITEM, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["menuItem"]

    assert data["name"] == menu_item.name
    assert data["url"] == menu_item.url
    assert data["page"] is None
