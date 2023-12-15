import json
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import assert_no_permission, get_graphql_content

DELETE_GIFT_CARD_MUTATION = """
    mutation DeleteGiftCard($id: ID!) {
        giftCardDelete(id: $id) {
            giftCard {
                id
            }
        }
    }
"""


def test_delete_gift_card_by_staff(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = staff_api_client.post_graphql(
        DELETE_GIFT_CARD_MUTATION,
        {"id": id},
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardDelete"]["giftCard"]

    assert data["id"] == id
    with pytest.raises(gift_card._meta.model.DoesNotExist):
        gift_card.refresh_from_db()


def test_delete_gift_card_by_staff_no_permission(staff_api_client, gift_card):
    # given
    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = staff_api_client.post_graphql(DELETE_GIFT_CARD_MUTATION, {"id": id})

    # then
    assert_no_permission(response)


def test_delete_gift_card_by_app(
    app_api_client, gift_card, permission_manage_gift_card
):
    # given
    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = app_api_client.post_graphql(
        DELETE_GIFT_CARD_MUTATION,
        {"id": id},
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardDelete"]["giftCard"]

    assert data["id"] == id
    with pytest.raises(gift_card._meta.model.DoesNotExist):
        gift_card.refresh_from_db()


def test_delete_gift_card_by_customer(app_api_client, gift_card):
    # given
    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = app_api_client.post_graphql(DELETE_GIFT_CARD_MUTATION, {"id": id})

    # then
    assert_no_permission(response)


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_gift_card_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = staff_api_client.post_graphql(
        DELETE_GIFT_CARD_MUTATION,
        {"id": id},
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardDelete"]["giftCard"]

    assert data["id"] == id
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": id,
                "is_active": gift_card.is_active,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.GIFT_CARD_DELETED,
        [any_webhook],
        gift_card,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )
