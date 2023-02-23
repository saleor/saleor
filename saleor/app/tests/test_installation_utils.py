import json
from unittest.mock import ANY, Mock, patch

import graphene
import pytest
import requests
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from ...core.utils.json_serializer import CustomJsonEncoder
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.payloads import generate_meta, generate_requestor
from ..installation_utils import (
    AppInstallationError,
    install_app,
    validate_app_install_response,
)
from ..models import App
from ..types import AppExtensionMount, AppExtensionTarget


def test_validate_app_install_response():
    error_message = "Test error msg"
    response = Mock(spec=requests.Response)
    response.raise_for_status.side_effect = requests.HTTPError
    response.json.return_value = {"error": {"message": error_message}}

    with pytest.raises(AppInstallationError) as error:
        validate_app_install_response(response)
    assert str(error.value) == error_message


@pytest.mark.parametrize("json_response", ({}, {"error": {}}, Exception))
def test_validate_app_install_response_when_wrong_error_message(json_response):
    response = Mock(spec=requests.Response)
    response.raise_for_status.side_effect = requests.HTTPError
    response.json.side_effect = json_response

    with pytest.raises(requests.HTTPError):
        validate_app_install_response(response)


def test_install_app_created_app(
    app_manifest, app_installation, monkeypatch, permission_manage_products
):
    # given
    app_manifest["permissions"] = ["MANAGE_PRODUCTS"]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    mocked_post = Mock()
    monkeypatch.setattr(requests, "post", mocked_post)

    app_installation.permissions.set([permission_manage_products])

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    mocked_post.assert_called_once_with(
        app_manifest["tokenTargetUrl"],
        headers={
            "Content-Type": "application/json",
            # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
            "X-Saleor-Domain": "mirumee.com",
            "Saleor-Domain": "mirumee.com",
            "Saleor-Api-Url": "http://mirumee.com/graphql/",
        },
        json={"auth_token": ANY},
        timeout=ANY,
    )
    assert App.objects.get().id == app.id
    assert list(app.permissions.all()) == [permission_manage_products]


def test_install_app_created_app_with_audience(
    app_manifest, app_installation, monkeypatch, site_settings
):
    # given
    audience = f"https://{site_settings.site.domain}.com/app-123"
    app_manifest["audience"] = audience
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    assert app.audience == audience


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_install_app_created_app_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    app_manifest,
    app_installation,
    monkeypatch,
    permission_manage_products,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    app_manifest["permissions"] = ["MANAGE_PRODUCTS"]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    app_installation.permissions.set([permission_manage_products])

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("App", app.id),
                "is_active": app.is_active,
                "name": app.name,
                "meta": generate_meta(requestor_data=generate_requestor()),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.APP_INSTALLED,
        [any_webhook],
        app,
        None,
    )


def test_install_app_with_extension(
    app_manifest,
    app_installation,
    monkeypatch,
    permission_manage_products,
    permission_manage_orders,
):
    # given
    label = "Create product with app"
    url = "http://127.0.0.1:8080/app-extension"
    app_manifest["permissions"] = ["MANAGE_PRODUCTS", "MANAGE_ORDERS"]
    app_manifest["extensions"] = [
        {
            "label": label,
            "url": url,
            "mount": "PRODUCT_OVERVIEW_CREATE",
            "permissions": ["MANAGE_PRODUCTS"],
        }
    ]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    app_installation.permissions.set(
        [permission_manage_products, permission_manage_orders]
    )

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    assert App.objects.get().id == app.id
    app_extension = app.extensions.get()

    assert app_extension.label == label
    assert app_extension.url == url
    assert app_extension.mount == AppExtensionMount.PRODUCT_OVERVIEW_CREATE
    assert app_extension.target == AppExtensionTarget.POPUP
    assert list(app_extension.permissions.all()) == [permission_manage_products]


@pytest.mark.parametrize(
    "app_permissions, extension_permissions",
    [
        ([], ["MANAGE_PRODUCTS"]),
        (["MANAGE_PRODUCTS"], ["MANAGE_PRODUCTS", "MANAGE_APPS"]),
    ],
)
def test_install_app_extension_permission_out_of_scope(
    app_permissions, extension_permissions, app_manifest, app_installation, monkeypatch
):
    # given
    label = "Create product with app"
    url = "http://127.0.0.1:8080/app-extension"
    view = "PRODUCT"
    type = "OVERVIEW"
    target = "CREATE"
    app_manifest["permissions"] = app_permissions
    app_manifest["extensions"] = [
        {
            "label": label,
            "url": url,
            "view": view,
            "type": type,
            "target": target,
            "permissions": extension_permissions,
        }
    ]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when & then
    with pytest.raises(ValidationError):
        install_app(app_installation, activate=True)


@pytest.mark.parametrize(
    "url",
    [
        "http:/127.0.0.1:8080/app",
        "127.0.0.1:8080/app",
        "",
        "/app",
        "www.example.com/app",
    ],
)
def test_install_app_extension_incorrect_url(
    url, app_manifest, app_installation, monkeypatch
):
    # given
    app_manifest["permissions"] = ["MANAGE_PRODUCTS"]
    app_manifest["extensions"] = [
        {
            "url": url,
            "label": "Create product with app",
            "view": "PRODUCT",
            "type": "OVERVIEW",
            "target": "CREATE",
            "permissions": ["MANAGE_PRODUCTS"],
        }
    ]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when & then
    with pytest.raises(ValidationError):
        install_app(app_installation, activate=True)


def test_install_app_extension_invalid_permission(
    app_manifest, app_installation, monkeypatch
):
    # given
    label = "Create product with app"
    url = "http://127.0.0.1:8080/app-extension"
    view = "PRODUCT"
    type = "OVERVIEW"
    target = "CREATE"
    app_manifest["permissions"] = ["MANAGE_PRODUCTS"]
    app_manifest["extensions"] = [
        {
            "label": label,
            "url": url,
            "view": view,
            "type": type,
            "target": target,
            "permissions": ["INVALID_PERM"],
        }
    ]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when & then
    with pytest.raises(ValidationError):
        install_app(app_installation, activate=True)


@pytest.mark.parametrize(
    "incorrect_field",
    [
        "view",
        "type",
        "target",
    ],
)
def test_install_app_extension_incorrect_values(
    incorrect_field, app_manifest, app_installation, monkeypatch
):
    # given
    label = "Create product with app"
    url = "http://127.0.0.1:8080/app-extension"
    view = "PRODUCT"
    type = "OVERVIEW"
    target = "CREATE"
    app_manifest["permissions"] = []
    app_manifest["extensions"] = [
        {
            "label": label,
            "url": url,
            "view": view,
            "type": type,
            "target": target,
            "permissions": ["MANAGE_PRODUCTS"],
        }
    ]
    app_manifest["extensions"][0][incorrect_field] = "wrong-value"
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when & then
    with pytest.raises(ValidationError):
        install_app(app_installation, activate=True)


def test_install_app_with_webhook(
    app_manifest, app_manifest_webhook, app_installation, monkeypatch
):
    # given
    custom_headers = {"X-Key": "Value"}
    app_manifest_webhook["customHeaders"] = custom_headers
    app_manifest["webhooks"] = [app_manifest_webhook]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    assert app.id == App.objects.get().id

    webhook = app.webhooks.get()
    assert webhook.name == app_manifest_webhook["name"]
    assert sorted(webhook.events.values_list("event_type", flat=True)) == sorted(
        app_manifest_webhook["events"]
    )
    assert webhook.subscription_query == app_manifest_webhook["query"]
    assert webhook.target_url == app_manifest_webhook["targetUrl"]
    assert webhook.is_active is True
    assert webhook.custom_headers == {"x-key": "Value"}


def test_install_app_webhook_incorrect_url(
    app_manifest, app_manifest_webhook, app_installation, monkeypatch
):
    # given
    app_manifest_webhook["targetUrl"] = "ftp://user:pass@app.example/deep/cover"
    app_manifest["webhooks"] = [app_manifest_webhook]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))

    # when & then
    with pytest.raises(ValidationError) as excinfo:
        install_app(app_installation, activate=True)

    error_dict = excinfo.value.error_dict
    assert "webhooks" in error_dict
    assert error_dict["webhooks"][0].message == "Invalid target url."


def test_install_app_webhook_incorrect_query(
    app_manifest, app_manifest_webhook, app_installation, monkeypatch
):
    # given
    app_manifest_webhook[
        "query"
    ] = """
        no {
            that's {
                not {
                    ... on a {
                        valid graphql {
                            query
                        }
                    }
                }
            }
        }
    """
    app_manifest["webhooks"] = [app_manifest_webhook]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))

    # when & then
    with pytest.raises(ValidationError) as excinfo:
        install_app(app_installation, activate=True)

    error_dict = excinfo.value.error_dict
    assert "webhooks" in error_dict
    assert "Subscription query is not valid:" in error_dict["webhooks"][0].message


def test_install_app_webhook_incorrect_custom_headers(
    app_manifest, app_manifest_webhook, app_installation, monkeypatch
):
    # given
    custom_headers = {"InvalidKey": "Value"}
    app_manifest_webhook["customHeaders"] = custom_headers
    app_manifest["webhooks"] = [app_manifest_webhook]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))

    # when & then
    with pytest.raises(ValidationError) as excinfo:
        install_app(app_installation, activate=True)

    error_dict = excinfo.value.error_dict
    assert "webhooks" in error_dict
    assert error_dict["webhooks"][0].message == (
        'Invalid custom headers: "InvalidKey" '
        'does not match allowed key pattern: "X-*" or "Authorization*".'
    )


def test_install_app_lack_of_token_target_url_in_manifest_data(
    app_manifest, app_installation, monkeypatch, permission_manage_products
):
    # given
    app_manifest.pop("tokenTargetUrl")

    app_manifest["permissions"] = ["MANAGE_PRODUCTS"]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    mocked_post = Mock()
    monkeypatch.setattr(requests, "post", mocked_post)

    app_installation.permissions.set([permission_manage_products])

    # when & then
    with pytest.raises(ValidationError) as excinfo:
        install_app(app_installation, activate=True)

    error_dict = excinfo.value.error_dict
    assert "tokenTargetUrl" in error_dict
    assert error_dict["tokenTargetUrl"][0].message == "Field required."
