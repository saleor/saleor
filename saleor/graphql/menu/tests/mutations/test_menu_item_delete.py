import json
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

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
    # given
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    variables = {"id": menu_item_id}

    # when
    response = staff_api_client.post_graphql(
        DELETE_MENU_ITEM_MUTATION, variables, permissions=[permission_manage_menus]
    )

    # then
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
        allow_replica=False,
    )
