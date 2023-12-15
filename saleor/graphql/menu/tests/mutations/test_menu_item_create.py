import json
from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....menu.models import MenuItem
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

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
    # given
    name = "item menu"
    url = "http://www.example.com"
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"name": name, "url": url, "menu_id": menu_id}

    # when
    response = staff_api_client.post_graphql(
        CREATE_MENU_ITEM_MUTATION, variables, permissions=[permission_manage_menus]
    )

    # then
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
        allow_replica=False,
    )
