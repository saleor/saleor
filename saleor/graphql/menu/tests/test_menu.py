import json
from unittest import mock

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ....core.utils.json_serializer import CustomJsonEncoder
from ....menu.error_codes import MenuErrorCode
from ....menu.models import Menu, MenuItem
from ....product.models import Category
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.payloads import generate_meta, generate_requestor
from ...menu.mutations import NavigationType, _validate_menu_item_instance
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)


def test_validate_menu_item_instance(category, page):
    _validate_menu_item_instance({"category": category}, "category", Category)
    with pytest.raises(ValidationError):
        _validate_menu_item_instance({"category": page}, "category", Category)

    # test that validation passes with empty values passed in input
    _validate_menu_item_instance({}, "category", Category)
    _validate_menu_item_instance({"category": None}, "category", Category)


QUERY_MENU = """
    query ($id: ID, $name: String, $slug: String){
        menu(
            id: $id,
            name: $name,
            slug: $slug
        ) {
            id
            name
            slug
        }
    }
    """


def test_menu_query_by_id(
    user_api_client,
    menu,
):
    variables = {"id": graphene.Node.to_global_id("Menu", menu.pk)}

    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)
    content = get_graphql_content(response)
    menu_data = content["data"]["menu"]
    assert menu_data is not None
    assert menu_data["name"] == menu.name


def test_staff_query_menu_by_invalid_id(staff_api_client, menu):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_MENU, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["menu"] is None


def test_staff_query_menu_with_invalid_object_type(staff_api_client, menu):
    variables = {"id": graphene.Node.to_global_id("Order", menu.pk)}
    response = staff_api_client.post_graphql(QUERY_MENU, variables)
    content = get_graphql_content(response)
    assert content["data"]["menu"] is None


def test_menu_query_by_name(
    user_api_client,
    menu,
):
    variables = {"name": menu.name}
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)
    content = get_graphql_content(response)
    menu_data = content["data"]["menu"]
    assert menu_data is not None
    assert menu_data["name"] == menu.name


def test_menu_query_by_slug(user_api_client):
    menu = Menu.objects.create(name="test_menu_name", slug="test_menu_name")
    variables = {"slug": menu.slug}
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)
    content = get_graphql_content(response)
    menu_data = content["data"]["menu"]
    assert menu_data is not None
    assert menu_data["name"] == menu.name
    assert menu_data["slug"] == menu.slug


def test_menu_query_error_when_id_and_name_provided(
    user_api_client,
    menu,
    graphql_log_handler,
):
    variables = {
        "id": graphene.Node.to_global_id("Menu", menu.pk),
        "name": menu.name,
    }
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_menu_query_error_when_no_param(
    user_api_client,
    menu,
    graphql_log_handler,
):
    variables = {}
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


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
    "menu_filter, count", [({"search": "Menu1"}, 1), ({"search": "Menu"}, 2)]
)
def test_menus_query_with_filter(
    menu_filter, count, staff_api_client, permission_manage_menus
):
    Menu.objects.create(name="Menu1", slug="Menu1")
    Menu.objects.create(name="Menu2", slug="Menu2")
    variables = {"filter": menu_filter}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    response = staff_api_client.post_graphql(QUERY_MENU_WITH_FILTER, variables)
    content = get_graphql_content(response)
    assert content["data"]["menus"]["totalCount"] == count


def test_menus_query_with_slug_filter(staff_api_client, permission_manage_menus):
    Menu.objects.create(name="Menu1", slug="Menu1")
    Menu.objects.create(name="Menu2", slug="Menu2")
    Menu.objects.create(name="Menu3", slug="menu3-slug")
    variables = {"filter": {"search": "menu3-slug"}}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    response = staff_api_client.post_graphql(QUERY_MENU_WITH_FILTER, variables)
    content = get_graphql_content(response)
    menus = content["data"]["menus"]["edges"]
    assert len(menus) == 1
    assert menus[0]["node"]["slug"] == "menu3-slug"


def test_menus_query_with_slug_list_filter(staff_api_client, permission_manage_menus):
    Menu.objects.create(name="Menu1", slug="Menu1")
    Menu.objects.create(name="Menu2", slug="Menu2")
    Menu.objects.create(name="Menu3", slug="Menu3")
    variables = {"filter": {"slug": ["Menu2", "Menu3"]}}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    response = staff_api_client.post_graphql(QUERY_MENU_WITH_FILTER, variables)
    content = get_graphql_content(response)
    menus = content["data"]["menus"]["edges"]
    slugs = [node["node"]["slug"] for node in menus]
    assert len(menus) == 2
    assert "Menu2" in slugs
    assert "Menu3" in slugs


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
    menu = Menu.objects.create(name="menu1", slug="menu1")
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


def test_menu_items_query(
    user_api_client, menu_with_items, published_collection, channel_USD, category
):
    query = """
    fragment SecondaryMenuSubItem on MenuItem {
        id
        name
        category {
            id
            name
        }
        url
        collection {
            id
            name
        }
        page {
            slug
        }
    }
    query menuitem($id: ID!, $channel: String) {
        menu(id: $id, channel: $channel) {
            items {
                ...SecondaryMenuSubItem
                children {
                ...SecondaryMenuSubItem
                }
            }
        }
    }
    """
    variables = {
        "id": graphene.Node.to_global_id("Menu", menu_with_items.pk),
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)

    items = content["data"]["menu"]["items"]
    assert not items[0]["category"]
    assert not items[0]["collection"]
    assert items[1]["children"][0]["category"]["name"] == category.name
    assert items[1]["children"][1]["collection"]["name"] == published_collection.name


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
    menu = Menu.objects.create(name="Menu1", slug="Menu1")
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
    menu = Menu.objects.create(name="Menu1", slug="Menu1")
    MenuItem.objects.create(name="MenuItem1", menu=menu)
    MenuItem.objects.create(name="MenuItem2", menu=menu)
    variables = {"sort_by": menu_item_sort}
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    response = staff_api_client.post_graphql(QUERY_MENU_ITEMS_WITH_SORT, variables)
    content = get_graphql_content(response)
    menu_items = content["data"]["menuItems"]["edges"]

    for order, menu_item_name in enumerate(result_order):
        assert menu_items[order]["node"]["name"] == menu_item_name


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
    query = QUERY_MENU_ITEM
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


CREATE_MENU_QUERY = """
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
                slug
                items {
                    id
                }
            }
        }
    }
    """


def test_create_menu(
    staff_api_client, published_collection, category, page, permission_manage_menus
):
    category_id = graphene.Node.to_global_id("Category", category.pk)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
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
        CREATE_MENU_QUERY, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    assert content["data"]["menuCreate"]["menu"]["name"] == "test-menu"
    assert content["data"]["menuCreate"]["menu"]["slug"] == "test-menu"


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_menu_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    published_collection,
    category,
    page,
    permission_manage_menus,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    category_id = graphene.Node.to_global_id("Category", category.pk)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    page_id = graphene.Node.to_global_id("Page", page.pk)
    url = "http://www.example.com"

    variables = {
        "name": "test-menu",
        "collection": collection_id,
        "category": category_id,
        "page": page_id,
        "url": url,
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_MENU_QUERY, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    menu = Menu.objects.last()

    # then
    assert content["data"]["menuCreate"]["menu"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Menu", menu.id),
                "slug": menu.slug,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.MENU_CREATED,
        [any_webhook],
        menu,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_create_menu_slug_already_exists(
    staff_api_client, collection, category, page, permission_manage_menus
):
    query = """
        mutation MenuCreate(
            $name: String!
        ) {
            menuCreate(input: { name: $name}) {
                menu {
                    name
                    slug
                }
            }
        }
    """

    existing_menu = Menu.objects.create(name="test-menu", slug="test-menu")
    variables = {
        "name": "test-menu",
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    assert content["data"]["menuCreate"]["menu"]["name"] == existing_menu.name
    assert content["data"]["menuCreate"]["menu"]["slug"] == f"{existing_menu.slug}-2"


def test_create_menu_provided_slug(
    staff_api_client, collection, category, page, permission_manage_menus
):
    query = """
        mutation MenuCreate(
            $name: String!
            $slug: String
        ) {
            menuCreate(input: { name: $name, slug: $slug}) {
                menu {
                    name
                    slug
                }
            }
        }
    """

    variables = {"name": "test-menu", "slug": "test-slug"}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    assert content["data"]["menuCreate"]["menu"]["name"] == "test-menu"
    assert content["data"]["menuCreate"]["menu"]["slug"] == "test-slug"


UPDATE_MENU_WITH_SLUG_MUTATION = """
    mutation updatemenu($id: ID!, $name: String! $slug: String) {
        menuUpdate(id: $id, input: {name: $name, slug: $slug}) {
            menu {
                name
                slug
            }
            errors {
                field
                code
            }
        }
    }
"""


def test_update_menu(staff_api_client, menu, permission_manage_menus):
    query = """
        mutation updatemenu($id: ID!, $name: String!) {
            menuUpdate(id: $id, input: {name: $name}) {
                menu {
                    name
                    slug
                }
                errors {
                    field
                    code
                }
            }
        }
    """
    name = "Blue oyster menu"
    variables = {"id": graphene.Node.to_global_id("Menu", menu.pk), "name": name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    assert content["data"]["menuUpdate"]["menu"]["name"] == name
    assert content["data"]["menuUpdate"]["menu"]["slug"] == menu.slug


def test_update_menu_with_slug(staff_api_client, menu, permission_manage_menus):
    name = "Blue oyster menu"
    variables = {
        "id": graphene.Node.to_global_id("Menu", menu.pk),
        "name": name,
        "slug": "new-slug",
    }
    response = staff_api_client.post_graphql(
        UPDATE_MENU_WITH_SLUG_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    assert content["data"]["menuUpdate"]["menu"]["name"] == name
    assert content["data"]["menuUpdate"]["menu"]["slug"] == "new-slug"


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_menu_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    menu,
    permission_manage_menus,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    name = "Blue oyster menu"
    variables = {
        "id": graphene.Node.to_global_id("Menu", menu.pk),
        "name": name,
        "slug": "new-slug",
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_MENU_WITH_SLUG_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["menuUpdate"]["menu"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "slug": variables["slug"],
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.MENU_UPDATED,
        [any_webhook],
        menu,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_update_menu_with_slug_already_exists(
    staff_api_client, menu, permission_manage_menus
):
    existing_menu = Menu.objects.create(name="test-slug-menu", slug="test-slug-menu")
    variables = {
        "id": graphene.Node.to_global_id("Menu", menu.pk),
        "name": "Blue oyster menu",
        "slug": existing_menu.slug,
    }
    response = staff_api_client.post_graphql(
        UPDATE_MENU_WITH_SLUG_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    error = content["data"]["menuUpdate"]["errors"][0]
    assert error["field"] == "slug"
    assert error["code"] == MenuErrorCode.UNIQUE.name


DELETE_MENU_MUTATION = """
    mutation deletemenu($id: ID!) {
        menuDelete(id: $id) {
            menu {
                name
            }
        }
    }
    """


def test_delete_menu(staff_api_client, menu, permission_manage_menus):
    # given
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"id": menu_id}

    # when
    response = staff_api_client.post_graphql(
        DELETE_MENU_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["menuDelete"]["menu"]["name"] == menu.name
    with pytest.raises(menu._meta.model.DoesNotExist):
        menu.refresh_from_db()


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_menu_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    menu,
    permission_manage_menus,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"id": menu_id}

    # when
    response = staff_api_client.post_graphql(
        DELETE_MENU_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["menuDelete"]["menu"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "slug": menu.slug,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.MENU_DELETED,
        [any_webhook],
        menu,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


CREATE_MENU_ITEM_MUTATION = """
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


def test_create_menu_item(staff_api_client, menu, permission_manage_menus):
    name = "item menu"
    url = "http://www.example.com"
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"name": name, "url": url, "menu_id": menu_id}
    response = staff_api_client.post_graphql(
        CREATE_MENU_ITEM_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    data = content["data"]["menuItemCreate"]["menuItem"]
    assert data["name"] == name
    assert data["url"] == url
    assert data["menu"]["name"] == menu.name


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_menu_item_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    menu,
    permission_manage_menus,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    name = "item menu"
    url = "http://www.example.com"
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"name": name, "url": url, "menu_id": menu_id}

    # when
    response = staff_api_client.post_graphql(
        CREATE_MENU_ITEM_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    menu_item = MenuItem.objects.last()

    # then
    assert content["data"]["menuItemCreate"]["menuItem"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("MenuItem", menu_item.id),
                "name": menu_item.name,
                "menu": {"id": menu_id},
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.MENU_ITEM_CREATED,
        [any_webhook],
        menu_item,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


UPDATE_MENU_ITEM_MUTATION = """
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


def test_update_menu_item(
    staff_api_client, menu, menu_item, page, permission_manage_menus
):
    # Menu item before update has url, but no page
    assert menu_item.url
    assert not menu_item.page
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    page_id = graphene.Node.to_global_id("Page", page.pk)
    variables = {"id": menu_item_id, "page": page_id}
    response = staff_api_client.post_graphql(
        UPDATE_MENU_ITEM_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    data = content["data"]["menuItemUpdate"]["menuItem"]
    assert data["page"]["id"] == page_id


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_menu_item_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    menu,
    menu_item,
    page,
    permission_manage_menus,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    # Menu item before update has url, but no page
    assert menu_item.url
    assert not menu_item.page
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    page_id = graphene.Node.to_global_id("Page", page.pk)
    variables = {"id": menu_item_id, "page": page_id}

    # when
    response = staff_api_client.post_graphql(
        UPDATE_MENU_ITEM_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["menuItemUpdate"]["menuItem"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": menu_item_id,
                "name": menu_item.name,
                "menu": {"id": graphene.Node.to_global_id("Menu", menu_item.menu_id)},
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.MENU_ITEM_UPDATED,
        [any_webhook],
        menu_item,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


DELETE_MENU_ITEM_MUTATION = """
    mutation deleteMenuItem($id: ID!) {
        menuItemDelete(id: $id) {
            menuItem {
                name
            }
        }
    }
    """


def test_delete_menu_item(staff_api_client, menu_item, permission_manage_menus):
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    variables = {"id": menu_item_id}
    response = staff_api_client.post_graphql(
        DELETE_MENU_ITEM_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)
    data = content["data"]["menuItemDelete"]["menuItem"]
    assert data["name"] == menu_item.name
    with pytest.raises(menu_item._meta.model.DoesNotExist):
        menu_item.refresh_from_db()


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_menu_item_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    menu_item,
    permission_manage_menus,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    variables = {"id": menu_item_id}

    # when
    response = staff_api_client.post_graphql(
        DELETE_MENU_ITEM_MUTATION, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["menuItemDelete"]["menuItem"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": menu_item_id,
                "name": menu_item.name,
                "menu": {"id": graphene.Node.to_global_id("Menu", menu_item.menu_id)},
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.MENU_ITEM_DELETED,
        [any_webhook],
        menu_item,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


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
mutation menuItemMove($menu: ID!, $moves: [MenuItemMoveInput!]!) {
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
        {"itemId": items_global_ids[0], "parentId": None, "sortOrder": 2},
        {"itemId": items_global_ids[1], "parentId": None, "sortOrder": None},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -2},
    ]

    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": items_global_ids[2], "parent": None, "children": []},
            {"id": items_global_ids[1], "parent": None, "children": []},
            {"id": items_global_ids[0], "parent": None, "children": []},
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


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_menu_reorder_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_menus,
    menu_item_list,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    assert len(menu_item_list) == 3

    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[0], "parentId": None, "sortOrder": 2},
        {"itemId": items_global_ids[1], "parentId": None, "sortOrder": None},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -2},
    ]

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    assert response["menu"]
    assert not response["errors"]
    assert mocked_webhook_trigger.call_count == 2


def test_menu_reorder_move_the_same_item_multiple_times(
    staff_api_client, permission_manage_menus, menu_item_list
):

    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    assert len(menu_item_list) == 3

    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[0], "parentId": None, "sortOrder": 1},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -1},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -1},
    ]

    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": items_global_ids[2], "parent": None, "children": []},
            {"id": items_global_ids[1], "parent": None, "children": []},
            {"id": items_global_ids[0], "parent": None, "children": []},
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


def test_menu_reorder_move_without_effect(
    staff_api_client, permission_manage_menus, menu_item_list
):

    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    assert len(menu_item_list) == 3

    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": 3},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -1},
    ]

    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": items_global_ids[0], "parent": None, "children": []},
            {"id": items_global_ids[2], "parent": None, "children": []},
            {"id": items_global_ids[1], "parent": None, "children": []},
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
        {"itemId": items_global_ids[0], "parentId": parent_global_id, "sortOrder": 3},
        {
            "itemId": items_global_ids[2],
            "parentId": parent_global_id,
            "sortOrder": None,
        },
        {"itemId": items_global_ids[3], "parentId": parent_global_id, "sortOrder": -3},
    ]

    expected_data = {
        "id": menu_id,
        "items": [
            {
                "id": items_global_ids[1],
                "parent": None,
                "children": [
                    {
                        "id": items_global_ids[3],
                        "parent": {"id": parent_global_id},
                        "children": [],
                    },
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


def test_menu_reorder_assign_and_unassign_parent(
    staff_api_client, permission_manage_menus, menu_item_list
):
    """Assign a menu item as parent of given menu items. Ensure the menu items
    are properly pushed at the bottom of the item's children.
    """

    menu_item_list = list(menu_item_list)
    assert len(menu_item_list) == 3

    menu_id = graphene.Node.to_global_id("Menu", menu_item_list[1].menu_id)

    root = menu_item_list[0]

    item1 = menu_item_list[1]
    item1.parent = root
    item1.save()

    item2 = menu_item_list[2]

    item2_child = MenuItem.objects.create(menu=root.menu, parent=item2, name="Child")

    root_id = graphene.Node.to_global_id("MenuItem", root.pk)
    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[2], "parentId": root_id, "sortOrder": 1},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": 1},
    ]

    expected_data = {
        "id": menu_id,
        "items": [
            {
                "id": items_global_ids[0],
                "parent": None,
                "children": [
                    {
                        "id": items_global_ids[1],
                        "parent": {"id": root_id},
                        "children": [],
                    },
                ],
            },
            {
                "id": items_global_ids[2],
                "parent": None,
                "children": [
                    {
                        "id": graphene.Node.to_global_id("MenuItem", item2_child.pk),
                        "parent": {"id": items_global_ids[2]},
                        "children": [],
                    },
                ],
            },
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


def test_menu_reorder_unassign_and_assign_parent(
    staff_api_client, permission_manage_menus, menu_item_list
):
    """Assign a menu item as parent of given menu items. Ensure the menu items
    are properly pushed at the bottom of the item's children.
    """

    menu_item_list = list(menu_item_list)
    assert len(menu_item_list) == 3

    menu_id = graphene.Node.to_global_id("Menu", menu_item_list[1].menu_id)

    root = menu_item_list[0]

    item1 = menu_item_list[1]
    item1.parent = root
    item1.save()

    item2 = menu_item_list[2]
    item2.parent = root
    item2.save()

    item2_child = MenuItem.objects.create(menu=root.menu, parent=item2, name="Child")

    root_id = graphene.Node.to_global_id("MenuItem", root.pk)
    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": 1},
        {"itemId": items_global_ids[2], "parentId": root_id, "sortOrder": -1},
    ]

    expected_data = {
        "id": menu_id,
        "items": [
            {
                "id": items_global_ids[0],
                "parent": None,
                "children": [
                    {
                        "id": items_global_ids[2],
                        "parent": {"id": root_id},
                        "children": [
                            {
                                "id": graphene.Node.to_global_id(
                                    "MenuItem", item2_child.pk
                                ),
                            },
                        ],
                    },
                    {
                        "id": items_global_ids[1],
                        "parent": {"id": root_id},
                        "children": [],
                    },
                ],
            },
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

    menu_without_items = Menu.objects.create(
        name="this menu has no items", slug="menu-no-items"
    )

    menu_id = graphene.Node.to_global_id("Menu", menu_without_items.id)
    node_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    moves = [{"itemId": node_id}]

    response = staff_api_client.post_graphql(
        QUERY_REORDER_MENU, {"moves": moves, "menu": menu_id}, [permission_manage_menus]
    )

    assert json.loads(response.content)["data"] == {
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


def test_menu_cannot_pass_an_invalid_menu_item_node_type(
    staff_api_client, staff_user, permission_manage_menus, menu_item
):
    """You shouldn't be able to pass a menu item node
    that is not an actual MenuType."""

    menu_without_items = Menu.objects.create(
        name="this menu has no items", slug="menu-without-items"
    )

    menu_id = graphene.Node.to_global_id("Menu", menu_without_items.id)
    node_id = graphene.Node.to_global_id("User", staff_user.pk)
    moves = [{"itemId": node_id}]

    response = staff_api_client.post_graphql(
        QUERY_REORDER_MENU, {"moves": moves, "menu": menu_id}, [permission_manage_menus]
    )

    assert json.loads(response.content)["data"] == {
        "menuItemMove": {
            "errors": [{"field": "item", "message": "Must receive a MenuItem id."}],
            "menu": None,
        }
    }
