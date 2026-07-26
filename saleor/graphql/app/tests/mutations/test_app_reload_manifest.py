import copy
import json
from unittest.mock import patch

import graphene
import pytest
import requests

from .....app.error_codes import AppErrorCode
from .....app.types import AppType
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook, WebhookEvent
from ....tests.utils import assert_no_permission, get_graphql_content

APP_RELOAD_MANIFEST_MUTATION = """
mutation AppReloadManifest(
  $id: ID!
  $dryRun: Boolean
  $expectedIncomingManifest: JSONString
) {
  appReloadManifest(
    id: $id
    dryRun: $dryRun
    expectedIncomingManifest: $expectedIncomingManifest
  ) {
    app {
      id
      name
    }
    preview {
      currentManifest
      incomingManifest
    }
    errors {
      field
      message
      code
    }
  }
}
"""


@pytest.fixture(autouse=True)
def _third_party_app(app):
    # The shared `app` fixture defaults to a LOCAL app; reloading a manifest
    # only makes sense for THIRDPARTY (manifest-installed) apps.
    app.type = AppType.THIRDPARTY
    app.save(update_fields=["type"])


@pytest.fixture
def reload_manifest(app, app_manifest, app_manifest_webhook):
    app_manifest["id"] = app.identifier
    app_manifest["webhooks"] = [app_manifest_webhook]
    return app_manifest


def _reload(
    staff_api_client,
    app,
    permissions,
    dry_run=False,
    expected_incoming_manifest=None,
    check_no_permissions=True,
):
    variables = {
        "id": graphene.Node.to_global_id("App", app.id),
        "dryRun": dry_run,
        "expectedIncomingManifest": expected_incoming_manifest,
    }
    response = staff_api_client.post_graphql(
        APP_RELOAD_MANIFEST_MUTATION,
        variables=variables,
        permissions=permissions,
        check_no_permissions=check_no_permissions,
    )
    content = get_graphql_content(response)
    return content["data"]["appReloadManifest"]


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_dry_run_applies_nothing(
    mocked_fetch,
    app,
    reload_manifest,
    staff_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
):
    # given
    mocked_fetch.return_value = reload_manifest
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    original_name = app.name

    # when
    data = _reload(staff_api_client, app, [permission_manage_apps], dry_run=True)

    # then
    assert data["errors"] == []
    current = json.loads(data["preview"]["currentManifest"])
    incoming = json.loads(data["preview"]["incomingManifest"])
    assert current["name"] == original_name
    assert incoming["name"] == reload_manifest["name"]
    assert [webhook["name"] for webhook in incoming["webhooks"]] == ["webhook"]
    app.refresh_from_db()
    assert app.name == original_name
    assert app.webhooks.exists() is False
    assert app.permissions.exists() is False


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_applies_changes(
    mocked_fetch,
    app,
    reload_manifest,
    staff_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
):
    # given
    mocked_fetch.return_value = reload_manifest
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    # A webhook matched by name: gets updated, keeps its is_active flag.
    matched = Webhook.objects.create(
        app=app,
        name="webhook",
        is_active=False,
        target_url="https://old.example/api/webhook",
        subscription_query="subscription { event { ... on OrderCreated { order { id } } } }",
    )
    WebhookEvent.objects.create(
        webhook=matched, event_type=WebhookEventAsyncType.ORDER_UPDATED
    )
    # A webhook absent from the manifest: gets deleted.
    unmatched = Webhook.objects.create(
        app=app,
        name="legacy-webhook",
        target_url="https://old.example/api/legacy",
    )

    # when
    data = _reload(staff_api_client, app, [permission_manage_apps])

    # then
    assert data["errors"] == []
    app.refresh_from_db()
    assert app.name == reload_manifest["name"]
    assert app.homepage_url == reload_manifest["homepageUrl"]
    permission_names = {permission.codename for permission in app.permissions.all()}
    assert permission_names == {"manage_products", "manage_users"}

    assert not Webhook.objects.filter(pk=unmatched.pk).exists()
    matched.refresh_from_db()
    assert matched.target_url == reload_manifest["webhooks"][0]["targetUrl"]
    assert matched.subscription_query == reload_manifest["webhooks"][0]["query"]
    assert matched.is_active is False  # admin's choice preserved
    event_types = set(matched.events.values_list("event_type", flat=True))
    assert event_types == {
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.CUSTOMER_CREATED,
        WebhookEventAsyncType.FULFILLMENT_CREATED,
    }


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_identifier_mismatch(
    mocked_fetch,
    app,
    reload_manifest,
    staff_api_client,
    permission_manage_apps,
):
    # given
    reload_manifest["id"] = "some.other.app"
    mocked_fetch.return_value = reload_manifest

    # when
    data = _reload(staff_api_client, app, [permission_manage_apps])

    # then
    assert data["app"] is None
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == AppErrorCode.INVALID.name


def test_app_reload_manifest_without_manifest_url(
    app, staff_api_client, permission_manage_apps
):
    # given
    app.manifest_url = None
    app.type = AppType.LOCAL
    app.save(update_fields=["manifest_url", "type"])

    # when
    data = _reload(staff_api_client, app, [permission_manage_apps])

    # then
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == AppErrorCode.INVALID.name


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_fetch_timeout(
    mocked_fetch, app, staff_api_client, permission_manage_apps
):
    # given
    mocked_fetch.side_effect = requests.Timeout()

    # when
    data = _reload(staff_api_client, app, [permission_manage_apps])

    # then
    assert data["errors"][0]["code"] == AppErrorCode.MANIFEST_URL_CANT_CONNECT.name


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_out_of_scope_permissions(
    mocked_fetch,
    app,
    reload_manifest,
    staff_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
):
    # given: staff user holds MANAGE_PRODUCTS but not MANAGE_USERS,
    # which the manifest requests.
    mocked_fetch.return_value = reload_manifest
    staff_user.user_permissions.add(permission_manage_products)

    # when
    data = _reload(staff_api_client, app, [permission_manage_apps])

    # then
    assert data["app"] is None
    assert data["errors"][0]["field"] == "permissions"
    assert data["errors"][0]["code"] == AppErrorCode.OUT_OF_SCOPE_PERMISSION.name
    app.refresh_from_db()
    assert app.permissions.exists() is False


def test_app_reload_manifest_removed_app(
    app_marked_to_be_removed, staff_api_client, permission_manage_apps
):
    # when
    data = _reload(staff_api_client, app_marked_to_be_removed, [permission_manage_apps])

    # then
    assert data["app"] is None
    assert data["errors"][0]["field"] == "id"


def test_app_reload_manifest_no_permission(app, staff_api_client):
    # when
    variables = {"id": graphene.Node.to_global_id("App", app.id), "dryRun": False}
    response = staff_api_client.post_graphql(
        APP_RELOAD_MANIFEST_MUTATION, variables=variables
    )

    # then
    assert_no_permission(response)


def test_app_reload_manifest_requires_staff_user(
    app, app_api_client, permission_manage_apps
):
    # given: an app (non-staff requestor) holding MANAGE_APPS still cannot
    # reload manifests.
    app_api_client.app.permissions.add(permission_manage_apps)

    # when
    variables = {"id": graphene.Node.to_global_id("App", app.id), "dryRun": False}
    response = app_api_client.post_graphql(
        APP_RELOAD_MANIFEST_MUTATION, variables=variables
    )

    # then
    assert_no_permission(response)


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_rejects_changed_manifest(
    mocked_fetch,
    app,
    reload_manifest,
    staff_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
):
    # given - a preview was generated, then the manifest changed before apply.
    # Each fetch returns a fresh copy, mirroring two separate GraphQL requests
    # (clean_manifest_data mutates the dict it is given).
    mocked_fetch.side_effect = lambda *args, **kwargs: copy.deepcopy(reload_manifest)
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    preview = _reload(staff_api_client, app, [permission_manage_apps], dry_run=True)
    stale_incoming = preview["preview"]["incomingManifest"]
    reload_manifest["name"] = "Changed since preview"

    # when - apply passes the previously-previewed incoming manifest
    data = _reload(
        staff_api_client,
        app,
        [permission_manage_apps],
        expected_incoming_manifest=stale_incoming,
        check_no_permissions=False,
    )

    # then - the mutation refuses to apply the unreviewed change
    assert data["app"] is None
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == AppErrorCode.INVALID.name
    app.refresh_from_db()
    assert app.name != "Changed since preview"


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_applies_when_manifest_unchanged(
    mocked_fetch,
    app,
    reload_manifest,
    staff_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
):
    # given
    mocked_fetch.side_effect = lambda *args, **kwargs: copy.deepcopy(reload_manifest)
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    preview = _reload(staff_api_client, app, [permission_manage_apps], dry_run=True)
    incoming = preview["preview"]["incomingManifest"]

    # when - the manifest is unchanged since the preview
    data = _reload(
        staff_api_client,
        app,
        [permission_manage_apps],
        expected_incoming_manifest=incoming,
        check_no_permissions=False,
    )

    # then
    assert data["errors"] == []
    app.refresh_from_db()
    assert app.name == reload_manifest["name"]


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_dry_run_preview_has_sorted_keys(
    mocked_fetch,
    app,
    reload_manifest,
    app_manifest_webhook,
    staff_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
):
    # given - a webhook with custom headers in non-sorted order
    app_manifest_webhook["customHeaders"] = {"X-Zeta": "1", "X-Alpha": "2"}
    mocked_fetch.return_value = reload_manifest
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)

    # when
    data = _reload(staff_api_client, app, [permission_manage_apps], dry_run=True)

    # then - the preview JSON is canonical (keys sorted), so the dashboard's
    # string comparison is stable
    incoming = data["preview"]["incomingManifest"]
    assert incoming == json.dumps(json.loads(incoming), sort_keys=True)


@patch("saleor.graphql.app.mutations.app_fetch_manifest.fetch_manifest")
def test_app_reload_manifest_rejects_overlong_name(
    mocked_fetch,
    app,
    reload_manifest,
    staff_api_client,
    staff_user,
    permission_manage_apps,
    permission_manage_products,
    permission_manage_users,
):
    # given - a manifest name longer than the App.name column (60 chars)
    reload_manifest["name"] = "x" * 61
    mocked_fetch.return_value = reload_manifest
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)

    # when
    data = _reload(staff_api_client, app, [permission_manage_apps])

    # then - a clean validation error, not a DataError/500
    assert data["app"] is None
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["code"] == AppErrorCode.INVALID.name
