import json
from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

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
    # given
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

    # then
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


def test_add_more_than_one_item(
    staff_api_client, menu, menu_item, page, permission_manage_menus
):
    # given
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

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["menuItemUpdate"]["errors"][0]
    assert data["message"] == "More than one item provided."
