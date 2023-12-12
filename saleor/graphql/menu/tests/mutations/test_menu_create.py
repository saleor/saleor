import json
from unittest import mock

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....menu.models import Menu
from .....product.models import Category
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....menu.mutations.menu_item_create import _validate_menu_item_instance
from ....tests.utils import get_graphql_content


def test_validate_menu_item_instance(category, page):
    _validate_menu_item_instance({"category": category}, "category", Category)
    with pytest.raises(ValidationError):
        _validate_menu_item_instance({"category": page}, "category", Category)

    # test that validation passes with empty values passed in input
    _validate_menu_item_instance({}, "category", Category)
    _validate_menu_item_instance({"category": None}, "category", Category)


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
    # given
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

    # then
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
        allow_replica=False,
    )


def test_create_menu_slug_already_exists(
    staff_api_client, collection, category, page, permission_manage_menus
):
    # given
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

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["menuCreate"]["menu"]["name"] == existing_menu.name
    assert content["data"]["menuCreate"]["menu"]["slug"] == f"{existing_menu.slug}-2"


def test_create_menu_provided_slug(
    staff_api_client, collection, category, page, permission_manage_menus
):
    # given
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

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["menuCreate"]["menu"]["name"] == "test-menu"
    assert content["data"]["menuCreate"]["menu"]["slug"] == "test-slug"
