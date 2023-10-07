from unittest import mock

import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.models import GiftCard, GiftCardEvent
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_GIFT_CARD_BULK_DEACTIVATE = """
    mutation GiftCardBulkDeactivate($ids: [ID!]!) {
        giftCardBulkDeactivate(ids: $ids) {
            count
            errors {
                code
                field
            }
        }
    }
"""


def test_gift_card_bulk_deactivate_by_staff(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    permission_manage_gift_card,
):
    # given
    gift_cards = [gift_card, gift_card_expiry_date]

    ids = [graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_cards]
    variables = {"ids": ids}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_GIFT_CARD_BULK_DEACTIVATE,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardBulkDeactivate"]

    assert (
        GiftCard.objects.filter(
            id__in=[card.id for card in gift_cards], is_active=False
        ).count()
        == 2
    )

    assert data["count"] == len(ids)
    events = GiftCardEvent.objects.all()
    assert events.count() == 2
    assert {event.gift_card_id for event in events} == {
        gift_card.id,
        gift_card_expiry_date.id,
    }
    assert {event.type for event in events} == {GiftCardEvents.DEACTIVATED}


def test_gift_card_bulk_deactivate_by_app(
    app_api_client,
    gift_card,
    gift_card_expiry_date,
    permission_manage_gift_card,
):
    # given
    gift_cards = [gift_card, gift_card_expiry_date]

    ids = [graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_cards]
    variables = {"ids": ids}

    # when
    response = app_api_client.post_graphql(
        MUTATION_GIFT_CARD_BULK_DEACTIVATE,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardBulkDeactivate"]

    assert (
        GiftCard.objects.filter(
            id__in=[card.id for card in gift_cards], is_active=False
        ).count()
        == 2
    )

    assert data["count"] == len(ids)
    events = GiftCardEvent.objects.all()
    assert events.count() == len(ids)
    assert {event.gift_card_id for event in events} == {card.id for card in gift_cards}
    assert {event.type for event in events} == {GiftCardEvents.DEACTIVATED}


def test_gift_card_bulk_deactivate_all_cards_already_inactive(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    permission_manage_gift_card,
):
    # given
    gift_cards = [gift_card, gift_card_expiry_date]
    for card in gift_cards:
        card.is_active = False
    GiftCard.objects.bulk_update(gift_cards, ["is_active"])

    ids = [graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_cards]
    variables = {"ids": ids}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_GIFT_CARD_BULK_DEACTIVATE,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardBulkDeactivate"]

    assert data["count"] == len(ids)
    events = GiftCardEvent.objects.all()
    assert events.count() == 0


def test_gift_card_bulk_deactivate_by_customer(
    api_client, gift_card, gift_card_expiry_date
):
    # given
    gift_cards = [gift_card, gift_card_expiry_date]

    ids = [graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_cards]
    variables = {"ids": ids}

    # when
    response = api_client.post_graphql(
        MUTATION_GIFT_CARD_BULK_DEACTIVATE,
        variables,
    )

    # then
    assert_no_permission(response)


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_gift_card_bulk_deactivate_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    permission_manage_gift_card,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    gift_cards = [gift_card, gift_card_expiry_date]

    ids = [graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_cards]
    variables = {"ids": ids}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_GIFT_CARD_BULK_DEACTIVATE,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardBulkDeactivate"]

    assert data["count"] == len(ids)
    assert mocked_webhook_trigger.call_count == len(ids)
