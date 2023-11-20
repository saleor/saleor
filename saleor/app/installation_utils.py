import logging
import time
from io import BytesIO
from typing import Optional, Union

import requests
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import DatabaseError
from django.urls import reverse
from requests import HTTPError, Response

from .. import schema_version
from ..app.headers import AppHeaders, DeprecatedAppHeaders
from ..celeryconf import app
from ..core.http_client import HTTPClient
from ..core.utils import build_absolute_uri, get_domain
from ..permission.enums import get_permission_names
from ..plugins.manager import PluginsManager
from ..thumbnail import ICON_MIME_TYPES
from ..thumbnail.utils import get_filename_from_url
from ..thumbnail.validators import validate_icon_image
from ..webhook.models import Webhook, WebhookEvent
from .error_codes import AppErrorCode
from .manifest_validations import clean_manifest_data
from .models import App, AppExtension, AppInstallation
from .types import AppExtensionTarget, AppType

MAX_ICON_FILE_SIZE = 1024 * 1024 * 10  # 10MB

logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)


class AppInstallationError(HTTPError):
    pass


def validate_app_install_response(response: Response):
    try:
        response.raise_for_status()
    except HTTPError as err:
        try:
            error_msg = str(response.json()["error"]["message"])
        except Exception:
            raise err
        raise AppInstallationError(
            error_msg, request=response.request, response=response
        )


def send_app_token(target_url: str, token: str):
    domain = get_domain()
    headers = {
        "Content-Type": "application/json",
        # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
        DeprecatedAppHeaders.DOMAIN: domain,
        AppHeaders.DOMAIN: domain,
        AppHeaders.API_URL: build_absolute_uri(reverse("api"), domain),
        AppHeaders.SCHEMA_VERSION: schema_version,
    }
    json_data = {"auth_token": token}
    response = HTTPClient.send_request(
        "POST",
        target_url,
        json=json_data,
        headers=headers,
        allow_redirects=False,
    )
    validate_app_install_response(response)


def fetch_icon_image(
    url: str,
    *,
    max_file_size=MAX_ICON_FILE_SIZE,
    timeout=settings.COMMON_REQUESTS_TIMEOUT,
) -> File:
    filename = get_filename_from_url(url)
    size_error_msg = f"File too big. Maximal icon image file size is {max_file_size}."
    code = AppErrorCode.INVALID.value
    fetch_start = time.monotonic()
    try:
        with HTTPClient.send_request(
            "GET", url, stream=True, timeout=timeout, allow_redirects=False
        ) as res:
            res.raise_for_status()
            content_type = res.headers.get("content-type")
            if content_type not in ICON_MIME_TYPES:
                raise ValidationError("Invalid file type.", code=code)
            try:
                if int(res.headers.get("content-length", 0)) > max_file_size:
                    raise ValidationError(size_error_msg, code=code)
            except (ValueError, TypeError):
                pass
            content = BytesIO()
            for chunk in res.iter_content(chunk_size=File.DEFAULT_CHUNK_SIZE):
                content.write(chunk)
                if content.tell() > max_file_size:
                    raise ValidationError(size_error_msg, code=code)
                timeout_in_secs = sum(timeout)
                if (time.monotonic() - fetch_start) > timeout_in_secs:
                    raise ValidationError(
                        "Timeout occurred while reading image file.",
                        code=AppErrorCode.MANIFEST_URL_CANT_CONNECT.value,
                    )
            content.seek(0)
            image_file = File(content, filename)
    except requests.RequestException:
        code = AppErrorCode.MANIFEST_URL_CANT_CONNECT.value
        raise ValidationError("Unable to fetch image.", code=code)

    validate_icon_image(image_file, code)
    return image_file


def fetch_brand_data(manifest_data, timeout=settings.COMMON_REQUESTS_TIMEOUT):
    brand_data = manifest_data.get("brand")
    if not brand_data:
        return None
    try:
        logo_url = brand_data["logo"]["default"]
        logo_file = fetch_icon_image(logo_url, timeout=timeout)
        brand_data["logo"]["default"] = logo_file
    except ValidationError as error:
        msg = "Fetching brand data failed for app:%r error:%r"
        logger.info(msg, manifest_data["id"], error, extra={"brand_data": brand_data})
        brand_data = None
    return brand_data


def _set_brand_data(brand_obj: Optional[Union[App, AppInstallation]], logo: File):
    if not brand_obj:
        return
    try:
        brand_obj.refresh_from_db()
    except ObjectDoesNotExist:
        return
    try:
        if not brand_obj.brand_logo_default:
            brand_obj.brand_logo_default.save(logo.name, logo, save=False)
            brand_obj.save(update_fields=["brand_logo_default"])
    except DatabaseError:
        # If object was already deleted from DB, remove created image
        default_storage.delete(brand_obj.brand_logo_default.name)


@app.task(bind=True, retry_backoff=2700, retry_kwargs={"max_retries": 5})
def fetch_brand_data_task(
    self, brand_data: dict, *, app_installation_id=None, app_id=None
):
    """Task to fetch app's brand data. Last retry delayed 24H."""
    app = App.objects.filter(id=app_id, removed_at__isnull=True).first()
    app_inst = AppInstallation.objects.filter(id=app_installation_id).first()
    if not app_inst or (app_inst and app_inst.brand_logo_default):
        if not app or (app and app.brand_logo_default):
            # App and AppInstall deleted or brand data already fetched
            return
    try:
        logo_img = fetch_icon_image(brand_data["logo"]["default"])
        _set_brand_data(app_inst, logo_img)
        _set_brand_data(app, logo_img)
    except ValidationError as error:
        extra = {
            "app_id": app_id,
            "app_installation_id": app_installation_id,
            "brand_data": brand_data,
        }
        task_logger.info("Fetching brand data failed. Error: %r", error, extra=extra)
        try:
            countdown = self.retry_backoff * (2**self.request.retries)
            raise self.retry(countdown=countdown, **self.retry_kwargs)
        except MaxRetriesExceededError:
            task_logger.info("Fetching brand data exceeded retry limit.", extra=extra)


def fetch_brand_data_async(
    manifest_data: dict,
    *,
    app_installation: Optional[AppInstallation] = None,
    app: Optional[App] = None,
):
    if brand_data := manifest_data.get("brand"):
        app_id = app.pk if app else None
        app_installation_id = app_installation.pk if app_installation else None
        fetch_brand_data_task.delay(
            brand_data, app_installation_id=app_installation_id, app_id=app_id
        )


def fetch_manifest(manifest_url: str, timeout=settings.COMMON_REQUESTS_TIMEOUT):
    headers = {AppHeaders.SCHEMA_VERSION: schema_version}
    response = HTTPClient.send_request(
        "GET", manifest_url, headers=headers, timeout=timeout, allow_redirects=False
    )
    response.raise_for_status()
    return response.json()


def install_app(app_installation: AppInstallation, activate: bool = False):
    manifest_data = fetch_manifest(app_installation.manifest_url)
    assigned_permissions = app_installation.permissions.all()

    manifest_data["permissions"] = get_permission_names(assigned_permissions)

    clean_manifest_data(manifest_data, raise_for_saleor_version=True)

    app = App.objects.create(
        name=app_installation.app_name,
        is_active=activate,
        identifier=manifest_data.get("id"),
        about_app=manifest_data.get("about"),
        data_privacy=manifest_data.get("dataPrivacy"),
        data_privacy_url=manifest_data.get("dataPrivacyUrl"),
        homepage_url=manifest_data.get("homepageUrl"),
        support_url=manifest_data.get("supportUrl"),
        configuration_url=manifest_data.get("configurationUrl"),
        app_url=manifest_data.get("appUrl"),
        version=manifest_data.get("version"),
        manifest_url=app_installation.manifest_url,
        type=AppType.THIRDPARTY,
        audience=manifest_data.get("audience"),
        is_installed=False,
        author=manifest_data.get("author"),
    )

    app.permissions.set(app_installation.permissions.all())
    for extension_data in manifest_data.get("extensions", []):
        extension = AppExtension.objects.create(
            app=app,
            label=extension_data.get("label"),
            url=extension_data.get("url"),
            mount=extension_data.get("mount"),
            target=extension_data.get("target", AppExtensionTarget.POPUP),
        )
        extension.permissions.set(extension_data.get("permissions", []))

    webhooks = Webhook.objects.bulk_create(
        Webhook(
            app=app,
            name=webhook["name"],
            is_active=webhook["isActive"],
            target_url=webhook["targetUrl"],
            subscription_query=webhook["query"],
            custom_headers=webhook.get("customHeaders", None),
        )
        for webhook in manifest_data.get("webhooks", [])
    )

    webhook_events = []
    for db_webhook, manifest_webhook in zip(
        webhooks, manifest_data.get("webhooks", [])
    ):
        for event_type in manifest_webhook["events"]:
            webhook_events.append(
                WebhookEvent(webhook=db_webhook, event_type=event_type)
            )
    WebhookEvent.objects.bulk_create(webhook_events)

    _, token = app.tokens.create(name="Default token")  # type: ignore[call-arg] # calling create on a related manager # noqa: E501

    try:
        send_app_token(target_url=manifest_data.get("tokenTargetUrl"), token=token)
    except requests.RequestException as e:
        fetch_brand_data_async(manifest_data, app_installation=app_installation)
        app.delete()
        raise e
    PluginsManager(plugins=settings.PLUGINS).app_installed(app)
    fetch_brand_data_async(manifest_data, app=app)
    return app, token
