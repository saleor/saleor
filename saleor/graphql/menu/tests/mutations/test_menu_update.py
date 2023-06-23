import json
from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....menu.error_codes import MenuErrorCode
from .....menu.models import Menu
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

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
    # given
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

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["menuUpdate"]["menu"]["name"] == name
    assert content["data"]["menuUpdate"]["menu"]["slug"] == menu.slug


def test_update_menu_with_slug(staff_api_client, menu, permission_manage_menus):
    # given
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

    # then
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
    # given
    existing_menu = Menu.objects.create(name="test-slug-menu", slug="test-slug-menu")
    variables = {
        "id": graphene.Node.to_global_id("Menu", menu.pk),
        "name": "Blue oyster menu",
        "slug": existing_menu.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_MENU_WITH_SLUG_MUTATION, variables, permissions=[permission_manage_menus]
    )

    # then
    content = get_graphql_content(response)
    error = content["data"]["menuUpdate"]["errors"][0]
    assert error["field"] == "slug"
    assert error["code"] == MenuErrorCode.UNIQUE.name
