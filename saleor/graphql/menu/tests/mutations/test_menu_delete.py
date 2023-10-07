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
