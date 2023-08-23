import json
from unittest.mock import ANY, Mock, patch

import graphene
import pytest
import requests
from celery.exceptions import Retry
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import DatabaseError
from freezegun import freeze_time
from requests_hardened import HTTPSession

from ... import __version__, schema_version
from ...core.utils.json_serializer import CustomJsonEncoder
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.payloads import generate_meta, generate_requestor
from ..error_codes import AppErrorCode
from ..installation_utils import (
    MAX_ICON_FILE_SIZE,
    AppInstallationError,
    fetch_brand_data_task,
    fetch_icon_image,
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
    mocked_get = Mock(return_value=Mock())
    mocked_get.return_value.json = Mock(return_value=app_manifest)
    mocked_post = Mock()

    def _side_effect(_self, method, *args, **kwargs):
        if method == "GET":
            func = mocked_get
        elif method == "POST":
            func = mocked_post
        else:
            raise NotImplementedError("Method not implemented", method)
        return func(method, *args, **kwargs)

    monkeypatch.setattr(HTTPSession, "request", _side_effect)

    app_installation.permissions.set([permission_manage_products])

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    mocked_get.assert_called_once_with(
        "GET",
        app_installation.manifest_url,
        headers={"Saleor-Schema-Version": schema_version},
        timeout=ANY,
        allow_redirects=False,
    )
    mocked_post.assert_called_once_with(
        "POST",
        app_manifest["tokenTargetUrl"],
        headers={
            "Content-Type": "application/json",
            # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
            "X-Saleor-Domain": "mirumee.com",
            "Saleor-Domain": "mirumee.com",
            "Saleor-Api-Url": "http://mirumee.com/graphql/",
            "Saleor-Schema-Version": schema_version,
        },
        json={"auth_token": ANY},
        timeout=ANY,
        allow_redirects=False,
    )
    assert App.objects.get().id == app.id
    assert list(app.permissions.all()) == [permission_manage_products]
    assert app.uuid is not None


def test_install_app_created_app_with_audience(
    app_manifest, app_installation, monkeypatch, site_settings
):
    # given
    audience = f"https://{site_settings.site.domain}.com/app-123"
    app_manifest["audience"] = audience
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    assert app.audience == audience


def test_install_app_with_required_saleor_version(
    app_manifest, app_installation, monkeypatch
):
    # given
    app_manifest["requiredSaleorVersion"] = f"^{__version__}"
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    assert App.objects.get().id == app.id


def test_install_app_when_saleor_version_unsupported(
    app_manifest, app_installation, monkeypatch
):
    # given
    app_manifest["requiredSaleorVersion"] = "<3.11"
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when
    with pytest.raises(ValidationError) as validation_error:
        install_app(app_installation, activate=True)

    # then
    errors = validation_error.value.error_dict["requiredSaleorVersion"]
    assert len(errors) == 1
    assert errors[0].code == AppErrorCode.UNSUPPORTED_SALEOR_VERSION.value


def test_install_app_with_author(app_manifest, app_installation, monkeypatch):
    # given
    app_manifest["author"] = "Acme Ltd"
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    assert App.objects.get().id == app.id
    assert app.author == app_manifest["author"]


def test_install_app_with_empty_author(app_manifest, app_installation, monkeypatch):
    # given
    app_manifest["author"] = " "
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when
    with pytest.raises(ValidationError) as validation_error:
        install_app(app_installation, activate=True)

    # then
    errors = validation_error.value.error_dict["author"]
    assert len(errors) == 1
    assert errors[0].code == AppErrorCode.INVALID.value


def test_install_app_with_brand_data(app_manifest, app_installation, monkeypatch):
    # given
    brand_data = {"logo": {"default": "https://example.com/logo.png"}}
    app_manifest["brand"] = brand_data
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())
    mocked_fetch_brand_data_task = Mock()
    monkeypatch.setattr(
        "saleor.app.installation_utils.fetch_brand_data_task.delay",
        mocked_fetch_brand_data_task,
    )

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    mocked_fetch_brand_data_task.assert_called_once_with(
        brand_data, app_installation_id=None, app_id=app.id
    )


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

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
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

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
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

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
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

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
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

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
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

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
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
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
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
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

    # when & then
    with pytest.raises(ValidationError) as excinfo:
        install_app(app_installation, activate=True)

    error_dict = excinfo.value.error_dict
    assert "webhooks" in error_dict
    assert error_dict["webhooks"][0].message == "Invalid target url."


@pytest.mark.parametrize("is_active", (True, False))
def test_install_app_with_webhook_is_active(
    is_active, app_manifest, app_manifest_webhook, app_installation, monkeypatch
):
    # given
    app_manifest_webhook["isActive"] = is_active
    app_manifest["webhooks"] = [app_manifest_webhook]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when
    app, _ = install_app(app_installation, activate=True)

    # then
    webhook = app.webhooks.get()
    assert webhook.is_active == is_active


def test_install_app_with_webhook_incorrect_is_active_value(
    app_manifest, app_manifest_webhook, app_installation, monkeypatch
):
    # given
    app_manifest_webhook["isActive"] = "incorrect value"
    app_manifest["webhooks"] = [app_manifest_webhook]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

    # when & then
    with pytest.raises(ValidationError) as excinfo:
        install_app(app_installation, activate=True)

    error_dict = excinfo.value.error_dict
    assert "webhooks" in error_dict
    assert error_dict["webhooks"][0].message == "Incorrect value for field: isActive."


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
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

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
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

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

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    mocked_post = Mock()
    monkeypatch.setattr(requests, "post", mocked_post)

    app_installation.permissions.set([permission_manage_products])

    # when & then
    with pytest.raises(ValidationError) as excinfo:
        install_app(app_installation, activate=True)

    error_dict = excinfo.value.error_dict
    assert "tokenTargetUrl" in error_dict
    assert error_dict["tokenTargetUrl"][0].message == "Field required."


@pytest.fixture
def image_response_mock():
    content_chunks = [b"fake ", b"image ", b"content"]
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"".join(content_chunks)
    mock_response.headers = {
        "content-type": "image/png",
        "content-length": str(len(mock_response.content)),
    }
    mock_response.iter_content.return_value = iter(content_chunks)
    return mock_response


@patch("saleor.app.installation_utils.validate_icon_image")
@patch.object(HTTPSession, "request")
def test_fetch_icon_image(
    mock_get_request, mock_validate_icon_image, image_response_mock
):
    # given
    image_file_format = "png"
    image_url = f"https://example.com/logo.{image_file_format}"
    mock_get_request.return_value.__enter__.return_value = image_response_mock

    # when
    image_file = fetch_icon_image(image_url)

    # then
    mock_get_request.assert_called_once_with(
        "GET", image_url, stream=True, timeout=ANY, allow_redirects=False
    )
    mock_validate_icon_image.assert_called_once_with(image_file, ANY)
    assert isinstance(image_file, File)
    assert image_file.read() == image_response_mock.content
    assert image_file.name.endswith(image_file_format)


@patch("saleor.app.installation_utils.validate_icon_image")
@patch.object(HTTPSession, "request")
def test_fetch_icon_image_invalid_type(
    mock_get_request, mock_validate_icon_image, image_response_mock
):
    mock_get_request.return_value.__enter__.return_value = image_response_mock
    image_response_mock.headers["content-type"] = "text/html"

    with pytest.raises(ValidationError) as error:
        fetch_icon_image("https://example.com/logo.png")
    assert error.value.code == AppErrorCode.INVALID.value
    mock_validate_icon_image.assert_not_called()


@patch.object(HTTPSession, "request")
def test_fetch_icon_image_content_length(mock_get_request, image_response_mock):
    mock_get_request.return_value.__enter__.return_value = image_response_mock
    image_response_mock.headers["content-length"] = MAX_ICON_FILE_SIZE + 1

    with pytest.raises(ValidationError) as error:
        fetch_icon_image("https://example.com/logo.png")
    assert error.value.code == AppErrorCode.INVALID.value
    assert "File too big. Maximal icon image file size is" in error.value.message


@patch.object(HTTPSession, "request")
def test_fetch_icon_image_file_too_big(mock_get_request, image_response_mock):
    def content_chunks():
        while True:
            yield b"0" * 1024

    mock_get_request.return_value.__enter__.return_value = image_response_mock
    image_response_mock.iter_content.return_value = content_chunks()

    with pytest.raises(ValidationError) as error:
        fetch_icon_image("https://example.com/logo.png")
    assert error.value.code == AppErrorCode.INVALID.value
    assert "File too big. Maximal icon image file size is" in error.value.message


@patch.object(HTTPSession, "request")
def test_fetch_icon_image_network_error(mock_get_request):
    mock_get_request.side_effect = requests.RequestException
    with pytest.raises(ValidationError) as error:
        fetch_icon_image("https://example.com/logo.png")
    assert error.value.code == AppErrorCode.MANIFEST_URL_CANT_CONNECT.value


@pytest.mark.parametrize("app_object", ["app", "app_installation"])
@patch("saleor.app.installation_utils.fetch_icon_image")
def test_fetch_brand_data_task(
    mock_fetch_icon_image, app_object, app_installation, app, media_root
):
    # given
    logo_url = "https://example.com/logo.png"
    fake_img_content = b"these are bytes"
    logo_img = ContentFile(fake_img_content, "logo.png")
    mock_fetch_icon_image.return_value = logo_img

    # when
    fetch_brand_data_task(
        {"logo": {"default": logo_url}},
        app_installation_id=None if app_object == "app" else app_installation.id,
        app_id=None if app_object != "app" else app.id,
    )

    # then
    app.refresh_from_db()
    app_installation.refresh_from_db()
    mock_fetch_icon_image.assert_called_once_with(logo_url)
    if app_object == "app":
        assert app.brand_logo_default.read() == fake_img_content
        assert bool(app_installation.brand_logo_default) is False
    else:
        assert app_installation.brand_logo_default.read() == fake_img_content
        assert bool(app.brand_logo_default) is False


@patch("saleor.app.installation_utils.fetch_icon_image")
def test_fetch_brand_data_task_terminated(
    mock_fetch_icon_image, app_installation, app, media_root
):
    app.delete(), app_installation.delete()
    fetch_brand_data_task({}, app_installation_id=app_installation.id, app_id=app.id)
    mock_fetch_icon_image.assert_not_called()


@patch("saleor.app.installation_utils.fetch_icon_image")
def test_fetch_brand_data_task_terminated_when_brand_data_fetched(
    mock_fetch_icon_image, app_installation, app, media_root
):
    app_installation.delete()
    app.brand_logo_default.save("logo.png", ContentFile(b"bytes"))
    fetch_brand_data_task({}, app_installation_id=app_installation.id, app_id=app.id)
    mock_fetch_icon_image.assert_not_called()


@patch("saleor.app.installation_utils.fetch_icon_image")
def test_fetch_brand_data_task_retry(
    mock_fetch_icon_image, app_installation, app, media_root
):
    # given
    brand_data = {"logo": {"default": "https://example.com/logo.png"}}
    mock_fetch_icon_image.side_effect = ValidationError("Fetch image error")

    # when
    with pytest.raises(Retry):
        fetch_brand_data_task(
            brand_data, app_installation_id=app_installation.id, app_id=app.id
        )


@patch("saleor.app.installation_utils.fetch_icon_image")
def test_fetch_brand_data_task_saving_brand_data(
    mock_fetch_icon_image, app_installation, app, media_root
):
    # given
    brand_data = {"logo": {"default": "https://example.com/logo.png"}}
    fake_img_content = b"these are bytes"
    logo_img = ContentFile(fake_img_content, "logo.png")

    def fake_fetch_icon_image(*args, **kwargs):
        # AppInstallation deleted during brand data fetching
        app_installation.delete()
        return logo_img

    mock_fetch_icon_image.side_effect = fake_fetch_icon_image

    # when
    fetch_brand_data_task(
        brand_data, app_installation_id=app_installation.id, app_id=app.id
    )

    # then
    app.refresh_from_db()
    assert app.brand_logo_default.read() == fake_img_content


@patch("saleor.app.installation_utils.AppInstallation.save", side_effect=DatabaseError)
@patch("saleor.app.installation_utils.default_storage.delete")
@patch("saleor.app.installation_utils.fetch_icon_image")
def test_fetch_brand_data_task_saving_deleted_object(
    mock_fetch_icon_image,
    mock_storage_delete,
    _mock_app_installation_save,
    app_installation,
    media_root,
):
    # given
    brand_data = {"logo": {"default": "https://example.com/logo.png"}}
    file_name = "logo.png"
    mock_fetch_icon_image.return_value = ContentFile(b"these are bytes", file_name)

    # when
    fetch_brand_data_task(brand_data, app_installation_id=app_installation.id)

    # then
    mock_storage_delete.assert_called_once_with(
        f"app-installation-brand-data/{file_name}"
    )
