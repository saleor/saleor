from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.models import Webhook, WebhookEvent
from ..installation_utils import (
    resync_app_from_manifest,
    serialize_app_as_manifest,
    serialize_manifest_for_preview,
)

SUBSCRIPTION_QUERY = "subscription { event { ... on OrderCreated { order { id } } } }"


def _manifest_data(app, **overrides):
    """Build manifest data in the shape produced by clean_manifest_data."""
    manifest_data = {
        "id": app.identifier,
        "name": "Reloaded app",
        "about": "About the reloaded app.",
        "version": "2.0",
        "author": "Saleor",
        "audience": None,
        "appUrl": "https://app.example/app",
        "configurationUrl": "https://app.example/configuration",
        "dataPrivacy": None,
        "dataPrivacyUrl": None,
        "homepageUrl": "https://app.example",
        "supportUrl": "https://app.example/support",
        "permissions": [],
        "extensions": [],
        "webhooks": [],
    }
    manifest_data.update(overrides)
    return manifest_data


def _manifest_webhook(**overrides):
    webhook = {
        "name": "order-webhook",
        "targetUrl": "https://app.example/api/webhook",
        "query": SUBSCRIPTION_QUERY,
        "events": [WebhookEventAsyncType.ORDER_CREATED],
        "isActive": True,
    }
    webhook.update(overrides)
    return webhook


def test_resync_creates_missing_webhooks(app):
    # given
    manifest_data = _manifest_data(app, webhooks=[_manifest_webhook()])

    # when
    resync_app_from_manifest(app, manifest_data)

    # then
    webhook = app.webhooks.get()
    assert webhook.name == "order-webhook"
    assert webhook.target_url == "https://app.example/api/webhook"
    assert webhook.is_active is True
    assert list(webhook.events.values_list("event_type", flat=True)) == [
        WebhookEventAsyncType.ORDER_CREATED
    ]


def test_resync_updates_matched_webhook_and_preserves_is_active(app):
    # given
    existing = Webhook.objects.create(
        app=app,
        name="order-webhook",
        is_active=False,
        target_url="https://old.example/api/webhook",
        subscription_query="subscription { event { __typename } }",
    )
    WebhookEvent.objects.create(
        webhook=existing, event_type=WebhookEventAsyncType.ORDER_UPDATED
    )
    manifest_data = _manifest_data(app, webhooks=[_manifest_webhook()])

    # when
    resync_app_from_manifest(app, manifest_data)

    # then
    existing.refresh_from_db()
    assert app.webhooks.count() == 1
    assert existing.target_url == "https://app.example/api/webhook"
    assert existing.subscription_query == SUBSCRIPTION_QUERY
    assert existing.is_active is False
    assert list(existing.events.values_list("event_type", flat=True)) == [
        WebhookEventAsyncType.ORDER_CREATED
    ]


def test_resync_deletes_webhooks_absent_from_manifest(app):
    # given
    Webhook.objects.create(
        app=app, name="legacy", target_url="https://old.example/api/legacy"
    )
    manifest_data = _manifest_data(app, webhooks=[_manifest_webhook()])

    # when
    resync_app_from_manifest(app, manifest_data)

    # then
    assert list(app.webhooks.values_list("name", flat=True)) == ["order-webhook"]


def test_resync_dedupes_duplicated_manifest_webhook_names(app):
    # given: the first occurrence of a duplicated name wins.
    manifest_data = _manifest_data(
        app,
        webhooks=[
            _manifest_webhook(targetUrl="https://app.example/api/first"),
            _manifest_webhook(targetUrl="https://app.example/api/second"),
        ],
    )

    # when
    resync_app_from_manifest(app, manifest_data)

    # then
    webhook = app.webhooks.get()
    assert webhook.target_url == "https://app.example/api/first"


def test_resync_updates_scalar_fields_and_permissions(app, permission_manage_products):
    # given
    app_is_active = app.is_active
    manifest_data = _manifest_data(app, permissions=[permission_manage_products])

    # when
    resync_app_from_manifest(app, manifest_data)

    # then
    app.refresh_from_db()
    assert app.name == "Reloaded app"
    assert app.about_app == "About the reloaded app."
    assert app.version == "2.0"
    assert app.homepage_url == "https://app.example"
    assert app.is_active == app_is_active
    assert [permission.codename for permission in app.permissions.all()] == [
        "manage_products"
    ]


def test_serialize_matches_after_resync(app, permission_manage_products):
    # given: once resynced, the app serializes exactly as its manifest —
    # this is the invariant the reload preview's "no changes" state relies on.
    manifest_data = _manifest_data(
        app,
        permissions=[permission_manage_products],
        webhooks=[
            _manifest_webhook(),
            _manifest_webhook(
                name="another-webhook",
                targetUrl="https://app.example/api/another",
                events=[
                    WebhookEventAsyncType.ORDER_UPDATED,
                    WebhookEventAsyncType.ORDER_CREATED,
                ],
            ),
        ],
    )

    # when
    resync_app_from_manifest(app, manifest_data)

    # then
    assert serialize_app_as_manifest(app) == serialize_manifest_for_preview(
        manifest_data
    )


def test_serialize_app_as_manifest_sorts_collections(app):
    # given
    for name in ["zeta", "alpha"]:
        webhook = Webhook.objects.create(
            app=app,
            name=name,
            target_url=f"https://app.example/api/{name}",
        )
        WebhookEvent.objects.bulk_create(
            WebhookEvent(webhook=webhook, event_type=event_type)
            for event_type in [
                WebhookEventAsyncType.ORDER_UPDATED,
                WebhookEventAsyncType.ORDER_CREATED,
            ]
        )

    # when
    serialized = serialize_app_as_manifest(app)

    # then
    assert [webhook["name"] for webhook in serialized["webhooks"]] == [
        "alpha",
        "zeta",
    ]
    assert serialized["webhooks"][0]["events"] == sorted(
        [
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_CREATED,
        ]
    )


def test_resync_converges_blank_identifier_app(app):
    # given - an app installed before identifiers were recorded
    app.identifier = ""
    app.save(update_fields=["identifier"])
    manifest_data = _manifest_data(app, id="saleor.reloaded.app")

    # when
    resync_app_from_manifest(app, manifest_data)

    # then - the app adopts the manifest id, so the preview reaches "up to date"
    app.refresh_from_db()
    assert app.identifier == "saleor.reloaded.app"
    assert serialize_app_as_manifest(app) == serialize_manifest_for_preview(
        manifest_data
    )


def test_resync_keeps_extension_ids_when_extensions_unchanged(app):
    # given - an app whose manifest keeps its single extension but changes a scalar
    from ...app.models import AppExtension

    extension = AppExtension.objects.create(
        app=app,
        label="Settings",
        url="https://app.example/settings",
        mount="navigation_catalog",
        target="popup",
        identifier="settings-ext",
    )
    manifest_extension = {
        "identifier": "settings-ext",
        "label": "Settings",
        "url": "https://app.example/settings",
        "mount": "navigation_catalog",
        "target": "popup",
        "permissions": [],
        "options": {},
    }
    manifest_data = _manifest_data(
        app, name="Renamed app", extensions=[manifest_extension]
    )

    # when
    resync_app_from_manifest(app, manifest_data)

    # then - the extension row is reused, not deleted and recreated
    assert list(app.extensions.values_list("pk", flat=True)) == [extension.pk]
    app.refresh_from_db()
    assert app.name == "Renamed app"


def test_resync_rebuilds_extensions_when_changed(app):
    # given
    from ...app.models import AppExtension

    old = AppExtension.objects.create(
        app=app,
        label="Old",
        url="https://app.example/old",
        mount="navigation_catalog",
        target="popup",
        identifier="old-ext",
    )
    manifest_data = _manifest_data(
        app,
        extensions=[
            {
                "identifier": "new-ext",
                "label": "New",
                "url": "https://app.example/new",
                "mount": "navigation_catalog",
                "target": "popup",
                "permissions": [],
                "options": {},
            }
        ],
    )

    # when
    resync_app_from_manifest(app, manifest_data)

    # then
    assert not AppExtension.objects.filter(pk=old.pk).exists()
    assert list(app.extensions.values_list("identifier", flat=True)) == ["new-ext"]


def test_serialize_matches_after_resync_with_custom_headers(app):
    # given - custom headers whose manifest key order differs from jsonb order
    manifest_data = _manifest_data(
        app,
        webhooks=[
            _manifest_webhook(
                customHeaders={"X-Zeta": "1", "X-Alpha": "2", "X-Mu": "3"}
            )
        ],
    )

    # when
    resync_app_from_manifest(app, manifest_data)

    # then - key order does not produce a phantom diff
    assert serialize_app_as_manifest(app) == serialize_manifest_for_preview(
        manifest_data
    )
