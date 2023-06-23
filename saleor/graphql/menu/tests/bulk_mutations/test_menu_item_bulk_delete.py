from unittest import mock

import graphene

from .....menu.models import MenuItem
from ....tests.utils import get_graphql_content

BULK_DELETE_MENU_ITEMS_MUTATION = """
    mutation menuItemBulkDelete($ids: [ID!]!) {
        menuItemBulkDelete(ids: $ids) {
            count
        }
    }
    """


def test_delete_menu_items(staff_api_client, menu_item_list, permission_manage_menus):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("MenuItem", menu_item.id)
            for menu_item in menu_item_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        BULK_DELETE_MENU_ITEMS_MUTATION,
        variables,
        permissions=[permission_manage_menus],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["menuItemBulkDelete"]["count"] == len(menu_item_list)
    assert not MenuItem.objects.filter(
        id__in=[menu_item.id for menu_item in menu_item_list]
    ).exists()


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_menu_items_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    menu_item_list,
    permission_manage_menus,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [
            graphene.Node.to_global_id("MenuItem", menu_item.id)
            for menu_item in menu_item_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        BULK_DELETE_MENU_ITEMS_MUTATION,
        variables,
        permissions=[permission_manage_menus],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["menuItemBulkDelete"]
    assert mocked_webhook_trigger.call_count == len(menu_item_list)


def test_delete_empty_list_of_ids(staff_api_client, permission_manage_menus):
    # given
    query = """
    mutation menuItemBulkDelete($ids: [ID!]!) {
        menuItemBulkDelete(ids: $ids) {
            count
        }
    }
    """
    menu_item_list = []
    variables = {"ids": menu_item_list}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["menuItemBulkDelete"]["count"] == len(menu_item_list)
