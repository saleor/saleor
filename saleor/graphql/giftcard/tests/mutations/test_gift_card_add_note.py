from datetime import date, timedelta
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

GIFT_CARD_ADD_NOTE_MUTATION = """
    mutation addNote($id: ID!, $message: String!) {
        giftCardAddNote(id: $id, input: {message: $message}) {
            errors {
                field
                message
                code
            }
            giftCard {
                id
            }
            event {
                user {
                    email
                }
                app {
                    name
                }
                message
            }
        }
    }
"""


def test_gift_card_add_note_as_staff_user(
    staff_api_client,
    permission_manage_apps,
    permission_manage_users,
    permission_manage_gift_card,
    gift_card,
    staff_user,
):
    # given
    assert not gift_card.events.all()
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)
    message = "nuclear note"
    variables = {"id": gift_card_id, "message": message}

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_ADD_NOTE_MUTATION,
        variables,
        permissions=[
            permission_manage_apps,
            permission_manage_users,
            permission_manage_gift_card,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardAddNote"]

    assert data["giftCard"]["id"] == gift_card_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["app"] is None
    assert data["event"]["message"] == message

    event = gift_card.events.get()
    assert event.type == GiftCardEvents.NOTE_ADDED
    assert event.user == staff_user
    assert event.parameters == {"message": message}


def test_gift_card_add_note_as_app(
    app_api_client,
    permission_manage_apps,
    permission_manage_users,
    permission_manage_gift_card,
    gift_card,
    staff_user,
):
    # given
    assert not gift_card.events.all()
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)
    message = "nuclear note"
    variables = {"id": gift_card_id, "message": message}

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_ADD_NOTE_MUTATION,
        variables,
        permissions=[
            permission_manage_apps,
            permission_manage_users,
            permission_manage_gift_card,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardAddNote"]

    assert data["giftCard"]["id"] == gift_card_id
    assert data["event"]["user"] is None
    assert data["event"]["app"]["name"] == app_api_client.app.name
    assert data["event"]["message"] == message

    event = gift_card.events.get()
    assert event.type == GiftCardEvents.NOTE_ADDED
    assert event.user is None
    assert event.app == app_api_client.app
    assert event.parameters == {"message": message}


@pytest.mark.parametrize(
    "message",
    (
        "",
        "   ",
    ),
)
def test_gift_card_add_note_fail_on_empty_message(
    message,
    staff_api_client,
    permission_manage_apps,
    permission_manage_users,
    permission_manage_gift_card,
    gift_card,
):
    # given
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)
    variables = {"id": gift_card_id, "message": message}

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_ADD_NOTE_MUTATION,
        variables,
        permissions=[
            permission_manage_apps,
            permission_manage_users,
            permission_manage_gift_card,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardAddNote"]
    assert data["errors"][0]["field"] == "message"
    assert data["errors"][0]["code"] == GiftCardErrorCode.REQUIRED.name


def test_gift_card_add_note_expired_card(
    staff_api_client,
    permission_manage_apps,
    permission_manage_users,
    permission_manage_gift_card,
    gift_card,
):
    # given
    staff_user = staff_api_client.user

    gift_card.expiry_date = date.today() - timedelta(days=1)
    gift_card.save(update_fields=["expiry_date"])

    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)
    message = "nuclear note"
    variables = {"id": gift_card_id, "message": message}

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_ADD_NOTE_MUTATION,
        variables,
        permissions=[
            permission_manage_apps,
            permission_manage_users,
            permission_manage_gift_card,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardAddNote"]

    assert data["giftCard"]["id"] == gift_card_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["app"] is None
    assert data["event"]["message"] == message

    event = gift_card.events.get()
    assert event.type == GiftCardEvents.NOTE_ADDED
    assert event.user == staff_user
    assert event.parameters == {"message": message}


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_gift_card_add_note_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_apps,
    permission_manage_users,
    permission_manage_gift_card,
    gift_card,
    staff_user,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)
    message = "nuclear note"
    variables = {"id": gift_card_id, "message": message}

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_ADD_NOTE_MUTATION,
        variables,
        permissions=[
            permission_manage_apps,
            permission_manage_users,
            permission_manage_gift_card,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardAddNote"]
    assert data["giftCard"]

    mocked_webhook_trigger.assert_called_once_with(
        {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
            "is_active": gift_card.is_active,
            "meta": generate_meta(
                requestor_data=generate_requestor(
                    SimpleLazyObject(lambda: staff_api_client.user)
                )
            ),
        },
        WebhookEventAsyncType.GIFT_CARD_UPDATED,
        [any_webhook],
        gift_card,
        SimpleLazyObject(lambda: staff_api_client.user),
    )
