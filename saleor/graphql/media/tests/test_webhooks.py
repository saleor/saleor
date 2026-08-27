import json
from unittest.mock import patch

import graphene
import pytest

from ....graphql.tests.utils import get_graphql_content
from ....plugins.manager import get_plugins_manager
from ....product import MediaOwnerTypes
from ....product.media import (
    MEDIA_OWNER_PERMISSION_MAP,
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.models import Webhook
from ....webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)
from ....webhook.utils import filter_webhooks_by_media_owner

MEDIA_CREATED_SUBSCRIPTION = """
    subscription {
      mediaCreated {
        media {
          __typename
          id
          alt
          mediaType
          ownerType
          ownerId
        }
        owner {
          __typename
          ... on Page { id title }
          ... on Product { id name }
          ... on Category { id name }
          ... on Collection { id name }
        }
      }
    }
"""

FILTERED_MEDIA_CREATED_SUBSCRIPTION = """
    subscription {
      mediaCreated(ownerTypes: [PAGE]) {
        media { id }
      }
    }
"""

WEBHOOK_CREATE_MUTATION = """
    mutation webhookCreate($input: WebhookCreateInput!) {
        webhookCreate(input: $input) {
            webhook { id }
            errors { code field message }
        }
    }
"""


def _create_webhook(app, query, event_type=WebhookEventAsyncType.MEDIA_CREATED):
    webhook = Webhook.objects.create(
        name="Media subscription",
        app=app,
        target_url="http://www.example.com/any",
        subscription_query=query,
    )
    webhook.events.create(event_type=event_type)
    return webhook


def test_subscription_payload_carries_media_and_owner(page, media_webhook_app):
    # given
    media = page.media.create(alt="an alt")
    webhook = _create_webhook(media_webhook_app, MEDIA_CREATED_SUBSCRIPTION)

    # when
    deliveries = create_deliveries_for_subscriptions(
        WebhookEventAsyncType.MEDIA_CREATED, media, [webhook]
    )

    # then
    assert len(deliveries) == 1
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload["data"]["mediaCreated"]["media"]["__typename"] == "PageMedia"
    assert payload["data"]["mediaCreated"]["media"]["id"] == graphene.Node.to_global_id(
        "PageMedia", media.pk
    )
    assert payload["data"]["mediaCreated"]["media"]["alt"] == "an alt"
    assert payload["data"]["mediaCreated"]["media"]["ownerType"] == "PAGE"
    assert payload["data"]["mediaCreated"]["owner"] == {
        "__typename": "Page",
        "id": graphene.Node.to_global_id("Page", page.pk),
        "title": page.title,
    }


@pytest.mark.parametrize("owner_type", MediaOwnerTypes.ALL)
def test_subscription_resolves_every_owner_type(
    owner_type, media_owner, media_webhook_app
):
    # given
    media = media_owner.media.create(alt="alt")
    webhook = _create_webhook(media_webhook_app, MEDIA_CREATED_SUBSCRIPTION)

    # when
    deliveries = create_deliveries_for_subscriptions(
        WebhookEventAsyncType.MEDIA_CREATED, media, [webhook]
    )

    # then
    assert len(deliveries) == 1
    payload = json.loads(deliveries[0].payload.get_payload())
    assert (
        payload["data"]["mediaCreated"]["media"]["__typename"]
        == OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type]
    )
    owner_payload = payload["data"]["mediaCreated"]["owner"]
    assert owner_payload["id"] == payload["data"]["mediaCreated"]["media"]["ownerId"]


def test_webhook_create_persists_owner_types_from_the_subscription(
    app_api_client, permission_manage_apps, permission_manage_pages
):
    # given
    app_api_client.app.permissions.add(permission_manage_apps, permission_manage_pages)
    variables = {
        "input": {
            "name": "Media webhook",
            "targetUrl": "https://www.example.com/hook",
            "query": FILTERED_MEDIA_CREATED_SUBSCRIPTION,
            "asyncEvents": ["MEDIA_CREATED"],
        }
    }

    # when
    response = app_api_client.post_graphql(WEBHOOK_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["webhookCreate"]["errors"] == []
    webhook = Webhook.objects.get()
    assert webhook.filterable_media_owner_types == [MediaOwnerTypes.PAGE]


def test_webhook_create_leaves_owner_types_empty_without_the_argument(
    app_api_client, permission_manage_apps, permission_manage_pages
):
    # given
    app_api_client.app.permissions.add(permission_manage_apps, permission_manage_pages)
    variables = {
        "input": {
            "name": "Media webhook",
            "targetUrl": "https://www.example.com/hook",
            "query": MEDIA_CREATED_SUBSCRIPTION,
            "asyncEvents": ["MEDIA_CREATED"],
        }
    }

    # when
    response = app_api_client.post_graphql(WEBHOOK_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["webhookCreate"]["errors"] == []
    webhook = Webhook.objects.get()
    assert webhook.filterable_media_owner_types == []


@pytest.mark.parametrize(
    ("_case", "filterable_owner_types", "owner_type", "is_delivered"),
    [
        ("no filter receives every owner type", [], MediaOwnerTypes.PRODUCT, True),
        ("no filter receives every owner type", [], MediaOwnerTypes.PAGE, True),
        (
            "filter matches the owner type",
            [MediaOwnerTypes.PAGE],
            MediaOwnerTypes.PAGE,
            True,
        ),
        (
            "filter excludes the owner type",
            [MediaOwnerTypes.PAGE],
            MediaOwnerTypes.PRODUCT,
            False,
        ),
    ],
)
def test_filter_webhooks_by_media_owner_applies_the_owner_type_filter(
    _case,
    filterable_owner_types,
    owner_type,
    is_delivered,
    media_webhook_app,
    permission_manage_products,
    permission_manage_pages,
):
    # given
    media_webhook_app.permissions.add(
        permission_manage_products, permission_manage_pages
    )
    webhook = _create_webhook(media_webhook_app, MEDIA_CREATED_SUBSCRIPTION)
    webhook.filterable_media_owner_types = filterable_owner_types
    webhook.save(update_fields=["filterable_media_owner_types"])

    # when
    filtered = filter_webhooks_by_media_owner([webhook], owner_type)

    # then
    assert filtered == ([webhook] if is_delivered else [])


@pytest.mark.parametrize(
    ("_case", "owner_type", "is_delivered"),
    [
        ("app holds the page permission", MediaOwnerTypes.PAGE, True),
        ("app lacks the product permission", MediaOwnerTypes.PRODUCT, False),
    ],
)
def test_filter_webhooks_by_media_owner_applies_the_owner_permission(
    _case, owner_type, is_delivered, media_webhook_app, permission_manage_pages
):
    # given
    media_webhook_app.permissions.add(permission_manage_pages)
    assert MEDIA_OWNER_PERMISSION_MAP[MediaOwnerTypes.PAGE].value.split(".")[1] == (
        permission_manage_pages.codename
    )
    webhook = _create_webhook(media_webhook_app, MEDIA_CREATED_SUBSCRIPTION)

    # when
    filtered = filter_webhooks_by_media_owner([webhook], owner_type)

    # then
    assert filtered == ([webhook] if is_delivered else [])


@patch(
    "saleor.plugins.webhook.plugin.trigger_webhooks_async",
)
def test_dispatch_skips_apps_without_the_owner_permission(
    mock_trigger,
    page,
    product,
    media_webhook_app,
    permission_manage_pages,
    settings,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    media_webhook_app.permissions.add(permission_manage_pages)
    _create_webhook(media_webhook_app, MEDIA_CREATED_SUBSCRIPTION)
    page_media = page.media.create(alt="page media")
    product_media = product.media.create(alt="product media")

    manager = get_plugins_manager(allow_replica=False)

    # when
    manager.media_created(page_media)
    manager.media_created(product_media)

    # then
    assert mock_trigger.call_count == 1
    assert mock_trigger.call_args.args[3] == page_media
