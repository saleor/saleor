from datetime import date, timedelta
from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import assert_no_permission, get_graphql_content

ACTIVATE_GIFT_CARD_MUTATION = """
    mutation giftCardActivate($id: ID!) {
        giftCardActivate(id: $id) {
            errors {
                field
                code
                message
            }
            giftCard {
                isActive
                events {
                    type
                    user {
                        email
                    }
                    app {
                        name
                    }
                }
            }
        }
    }
"""


def test_activate_gift_card_by_staff(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    assert not gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}

    # when
    response = staff_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardActivate"]["giftCard"]
    assert data["isActive"]
    events = data["events"]
    assert len(events) == 1
    assert events[0]["type"] == GiftCardEvents.ACTIVATED.upper()
    assert events[0]["user"]["email"] == staff_api_client.user.email
    assert events[0]["app"] is None


def test_activate_gift_card_by_app(
    app_api_client, gift_card, permission_manage_gift_card, permission_manage_users
):
    # given
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    assert not gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}

    # when
    response = app_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardActivate"]["giftCard"]
    assert data["isActive"]
    events = data["events"]
    assert len(events) == 1
    assert events[0]["type"] == GiftCardEvents.ACTIVATED.upper()
    assert events[0]["user"] is None
    assert events[0]["app"]["name"] == app_api_client.app.name


def test_activate_gift_card_by_customer(
    api_client,
    gift_card,
):
    # given
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    assert not gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}

    # when
    response = api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
    )

    # then
    assert_no_permission(response)


def test_activate_gift_card_without_premissions(staff_api_client, gift_card):
    # given
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}

    # when
    response = staff_api_client.post_graphql(ACTIVATE_GIFT_CARD_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_activate_active_gift_card(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    assert gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}

    # when
    response = staff_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardActivate"]["giftCard"]
    assert data["isActive"]
    assert not data["events"]


def test_activate_expired_gift_card(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card.is_active = False
    gift_card.expiry_date = date.today() - timedelta(days=1)
    gift_card.save(update_fields=["expiry_date", "is_active"])

    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}

    # when
    response = staff_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardActivate"]["errors"]
    data = content["data"]["giftCardActivate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == GiftCardErrorCode.EXPIRED_GIFT_CARD.name


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_activate_gift_card_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    assert not gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}

    # when
    response = staff_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardActivate"]["giftCard"]
    assert data["isActive"]

    mocked_webhook_trigger.assert_called_once_with(
        {
            "id": variables["id"],
            "is_active": True,
            "meta": generate_meta(
                requestor_data=generate_requestor(
                    SimpleLazyObject(lambda: staff_api_client.user)
                )
            ),
        },
        WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED,
        [any_webhook],
        gift_card,
        SimpleLazyObject(lambda: staff_api_client.user),
    )
