import logging
import time
from collections.abc import Iterable
from io import BytesIO

import requests
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import DatabaseError, transaction
from django.urls import reverse
from requests import HTTPError, Response

from .. import schema_version
from ..app.headers import AppHeaders, DeprecatedAppHeaders
from ..celeryconf import app
from ..core.db.connection import allow_writer
from ..core.http_client import HTTPClient
from ..core.utils import build_absolute_uri, get_domain
from ..permission.enums import get_permission_names
from ..plugins.manager import PluginsManager
from ..thumbnail import ICON_MIME_TYPES
from ..thumbnail.utils import get_filename_from_url
from ..thumbnail.validators import validate_icon_image
from ..webhook.models import Webhook, WebhookEvent
from .error_codes import AppErrorCode
from .manifest_validations import MANIFEST_SCALAR_FIELDS, clean_manifest_data
from .models import App, AppExtension, AppInstallation, AppToken
from .types import DEFAULT_APP_TARGET, AppType

MAX_ICON_FILE_SIZE = 1024 * 1024 * 10  # 10MB

logger = logging.getLogger(__name__)
task_logger = get_task_logger(f"{__name__}.celery")


class AppInstallationError(HTTPError):
    pass


def validate_app_install_response(response: Response):
    try:
        response.raise_for_status()
    except HTTPError as e:
        try:
            error_msg = str(response.json()["error"]["message"])
        except Exception:
            raise e from None
        raise AppInstallationError(
            error_msg, request=response.request, response=response
        ) from e


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
    except (ValidationError, OSError) as error:
        msg = "Fetching brand data failed for app:%r error:%r"
        logger.info(
            msg, manifest_data["id"], str(error), extra={"brand_data": brand_data}
        )
        brand_data = None
    return brand_data


def _set_brand_data(brand_obj: App | AppInstallation | None, logo: File):
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


@app.task(bind=True, retry_backoff=30, retry_kwargs={"max_retries": 5})
@allow_writer()
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
        task_logger.warning(
            "Fetching brand data failed. Error: %r", str(error), extra=extra
        )
        # Don't retry on validation errors image didn't pass validation when we tries again.
    except OSError as error:
        extra = {
            "app_id": app_id,
            "app_installation_id": app_installation_id,
            "brand_data": brand_data,
        }
        task_logger.info(
            "Fetching brand data failed. Error: %r", str(error), extra=extra
        )
        try:
            countdown = self.retry_backoff * (2**self.request.retries)
            raise self.retry(countdown=countdown, **self.retry_kwargs)
        except MaxRetriesExceededError:
            task_logger.info("Fetching brand data exceeded retry limit.", extra=extra)


def fetch_brand_data_async(
    manifest_data: dict,
    *,
    app_installation: AppInstallation | None = None,
    app: App | None = None,
):
    if brand_data := manifest_data.get("brand"):
        app_id = app.pk if app else None
        app_installation_id = app_installation.pk if app_installation else None
        fetch_brand_data_task.delay(
            brand_data, app_installation_id=app_installation_id, app_id=app_id
        )


def fetch_manifest(
    manifest_url: str,
    timeout=settings.COMMON_REQUESTS_TIMEOUT,
    max_retries: int = 0,
):
    headers = {AppHeaders.SCHEMA_VERSION: schema_version}
    connect_timeout, read_timeout = timeout

    def _get(attempt: int):
        response = HTTPClient.send_request(
            "GET",
            manifest_url,
            headers=headers,
            # Give subsequent retries an incremented connect timeout.
            timeout=(connect_timeout + attempt, read_timeout),
            allow_redirects=False,
        )
        response.raise_for_status()
        return response.json()

    for attempt in range(max_retries):
        try:
            return _get(attempt)
        except (requests.ConnectionError, requests.Timeout) as exc:
            logger.info(
                "Failed to fetch manifest (%s), retrying (attempt %d out of %d)...",
                exc,
                attempt + 1,
                max_retries + 1,
            )
    return _get(max_retries)  # final attempt, explicit return to satisfy ruff RET503


def _create_app_extension(app: App, extension_data: dict) -> AppExtension:
    # Manifest is already "clean" so values use serialization aliases (camelCase)
    options = extension_data.get("options", {})
    new_tab_target = options.get("newTabTarget")
    widget_target = options.get("widgetTarget")

    # Ensure proper extraction of the method values from the options
    http_target_method = None

    if (
        new_tab_target
        and isinstance(new_tab_target, dict)
        and "method" in new_tab_target
    ):
        http_target_method = new_tab_target["method"]

    if widget_target and isinstance(widget_target, dict) and "method" in widget_target:
        http_target_method = widget_target["method"]

    extension = AppExtension.objects.create(
        app=app,
        label=extension_data.get("label"),
        url=extension_data.get("url"),
        mount=extension_data.get("mount"),
        target=extension_data.get("target", DEFAULT_APP_TARGET),
        http_target_method=http_target_method,
        settings=extension_data.get("options", {}),
        identifier=extension_data.get("identifier"),
    )
    extension.permissions.set(extension_data.get("permissions", []))
    return extension


def _create_manifest_webhooks(app: App, manifest_webhooks: list[dict]) -> list[Webhook]:
    """Create webhooks (and their events) from cleaned manifest webhook data.

    Shared by install and reload so the two paths can never build webhook rows
    differently. The caller decides which webhooks to create (e.g. reload passes
    only the to-create subset).
    """
    webhooks = Webhook.objects.bulk_create(
        Webhook(
            app=app,
            name=webhook["name"],
            is_active=webhook["isActive"],
            target_url=webhook["targetUrl"],
            subscription_query=webhook["query"],
            custom_headers=webhook.get("customHeaders", None),
        )
        for webhook in manifest_webhooks
    )
    WebhookEvent.objects.bulk_create(
        WebhookEvent(webhook=db_webhook, event_type=event_type)
        for db_webhook, manifest_webhook in zip(
            webhooks, manifest_webhooks, strict=True
        )
        for event_type in manifest_webhook["events"]
    )
    return webhooks


def install_app(
    app_installation: AppInstallation, activate: bool = False
) -> tuple[App, AppToken | None]:
    manifest_data = fetch_manifest(app_installation.manifest_url, max_retries=2)
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
        _create_app_extension(app, extension_data)

    _create_manifest_webhooks(app, manifest_data.get("webhooks", []))

    token = None
    if tokent_target_url := manifest_data.get("tokenTargetUrl"):
        _, token = app.tokens.create(name="Default token")  # type: ignore[call-arg] # calling create on a related manager # noqa: E501

        try:
            send_app_token(target_url=tokent_target_url, token=token)
        except requests.RequestException as e:
            fetch_brand_data_async(manifest_data, app_installation=app_installation)
            app.delete()
            raise e
    PluginsManager(plugins=settings.PLUGINS).app_installed(app)
    fetch_brand_data_async(manifest_data, app=app)
    return app, token


def _dedupe_manifest_webhooks(manifest_webhooks: list[dict]) -> list[dict]:
    """Drop manifest webhooks with a duplicated name, keeping the first occurrence.

    Webhooks are matched by name during a manifest reload; duplicated names in
    a manifest are the app author's bug and are resolved deterministically.
    """
    seen: set[str] = set()
    deduped = []
    for webhook in manifest_webhooks:
        if webhook["name"] in seen:
            continue
        seen.add(webhook["name"])
        deduped.append(webhook)
    return deduped


def canonicalize_manifest_json(value):
    """Recursively sort dict keys so equal data serializes to an identical string.

    JSONField (jsonb) values return from Postgres in normalized — not authored —
    key order, so two semantically-equal manifests can dump to different JSON
    strings. Sorting keys before the value is handed to the JSONString scalar
    keeps the manifest-reload preview diff free of phantom key-order noise.
    """
    if isinstance(value, dict):
        return {key: canonicalize_manifest_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonicalize_manifest_json(item) for item in value]
    return value


def _serialize_webhook_for_preview(
    name: str, target_url: str, query: str | None, events: Iterable[str], custom_headers
) -> dict:
    return {
        "name": name,
        "targetUrl": target_url,
        "query": query or "",
        "events": sorted(events),
        "customHeaders": custom_headers or {},
    }


def _serialize_extension_for_preview(
    identifier, label, url, mount, target, permission_names: Iterable[str], options
) -> dict:
    return {
        "identifier": identifier,
        "label": label,
        "url": url,
        "mount": mount,
        "target": target,
        "permissions": sorted(permission_names),
        "options": options or {},
    }


def _serialize_app_extensions(app: App) -> list[dict]:
    return sorted(
        (
            _serialize_extension_for_preview(
                extension.identifier,
                extension.label,
                extension.url,
                extension.mount,
                extension.target,
                get_permission_names(extension.permissions.all()),
                extension.settings,
            )
            for extension in app.extensions.prefetch_related("permissions")
        ),
        key=lambda extension: (extension["identifier"] or "", extension["label"]),
    )


def _serialize_manifest_extensions(manifest_data: dict) -> list[dict]:
    return sorted(
        (
            _serialize_extension_for_preview(
                extension.get("identifier"),
                extension.get("label"),
                extension.get("url"),
                extension.get("mount"),
                extension.get("target", DEFAULT_APP_TARGET),
                get_permission_names(extension.get("permissions", [])),
                extension.get("options", {}),
            )
            for extension in manifest_data.get("extensions", [])
        ),
        key=lambda extension: (extension["identifier"] or "", extension["label"]),
    )


def _serialize_app_webhooks(app: App) -> list[dict]:
    return sorted(
        (
            _serialize_webhook_for_preview(
                webhook.name,
                webhook.target_url,
                webhook.subscription_query,
                (event.event_type for event in webhook.events.all()),
                webhook.custom_headers,
            )
            for webhook in app.webhooks.prefetch_related("events")
        ),
        key=lambda webhook: webhook["name"],
    )


def _serialize_manifest_webhooks(manifest_data: dict) -> list[dict]:
    return sorted(
        (
            _serialize_webhook_for_preview(
                webhook["name"],
                webhook["targetUrl"],
                webhook["query"],
                webhook["events"],
                webhook.get("customHeaders"),
            )
            for webhook in _dedupe_manifest_webhooks(manifest_data.get("webhooks", []))
        ),
        key=lambda webhook: webhook["name"],
    )


def serialize_app_as_manifest(app: App) -> dict:
    """Serialize an installed app's state into the manifest shape.

    Covers only the fields a manifest reload applies (scalar fields,
    permissions, extensions, webhooks) so it can be compared against
    ``serialize_manifest_for_preview`` output with no diff noise.
    """
    manifest = {
        manifest_key: getattr(app, attr)
        for manifest_key, attr in MANIFEST_SCALAR_FIELDS
    }
    manifest["id"] = app.identifier
    manifest["permissions"] = sorted(get_permission_names(app.permissions.all()))
    manifest["extensions"] = _serialize_app_extensions(app)
    manifest["webhooks"] = _serialize_app_webhooks(app)
    return manifest


def serialize_manifest_for_preview(manifest_data: dict) -> dict:
    """Serialize cleaned manifest data into the same shape as ``serialize_app_as_manifest``."""
    manifest = {
        manifest_key: manifest_data.get(manifest_key)
        for manifest_key, _ in MANIFEST_SCALAR_FIELDS
    }
    manifest["id"] = manifest_data.get("id")
    manifest["permissions"] = sorted(
        get_permission_names(manifest_data.get("permissions", []))
    )
    manifest["extensions"] = _serialize_manifest_extensions(manifest_data)
    manifest["webhooks"] = _serialize_manifest_webhooks(manifest_data)
    return manifest


def _resync_app_webhooks(app: App, manifest_webhooks: list[dict]):
    """Reconcile the app's webhooks with its manifest webhooks.

    Webhooks are matched by name — the only identity a manifest webhook has.
    Matched webhooks are updated in place, keeping their ``is_active`` flag
    (an admin's activation choice survives a reload) and ``secret_key``.
    A webhook renamed in the manifest is therefore deleted and recreated.
    """
    manifest_webhooks = _dedupe_manifest_webhooks(manifest_webhooks)
    existing_by_name: dict[str, Webhook] = {}
    for webhook in app.webhooks.order_by("pk").prefetch_related("events"):
        # Duplicated names among existing webhooks: the first one is matchable,
        # the rest are deleted below as unmatched.
        existing_by_name.setdefault(webhook.name, webhook)

    matched_ids = set()
    webhooks_to_create = []
    for manifest_webhook in manifest_webhooks:
        existing = existing_by_name.get(manifest_webhook["name"])
        if existing is None:
            webhooks_to_create.append(manifest_webhook)
            continue

        matched_ids.add(existing.pk)
        update_fields = []
        if existing.target_url != manifest_webhook["targetUrl"]:
            existing.target_url = manifest_webhook["targetUrl"]
            update_fields.append("target_url")
        if (existing.subscription_query or "") != (manifest_webhook["query"] or ""):
            existing.subscription_query = manifest_webhook["query"]
            update_fields.append("subscription_query")
        custom_headers = manifest_webhook.get("customHeaders") or {}
        if (existing.custom_headers or {}) != custom_headers:
            existing.custom_headers = custom_headers
            update_fields.append("custom_headers")
        if update_fields:
            existing.save(update_fields=update_fields)

        current_events = sorted(event.event_type for event in existing.events.all())
        manifest_events = sorted(manifest_webhook["events"])
        if current_events != manifest_events:
            existing.events.all().delete()
            WebhookEvent.objects.bulk_create(
                WebhookEvent(webhook=existing, event_type=event_type)
                for event_type in manifest_events
            )

    app.webhooks.exclude(pk__in=matched_ids).delete()

    _create_manifest_webhooks(app, webhooks_to_create)


def resync_app_from_manifest(app: App, manifest_data: dict) -> App:
    """Update an installed app in place from its cleaned manifest data.

    Applies the manifest's scalar fields, identifier, permissions, extensions
    and webhooks. The app's ``is_active`` flag, tokens and existing webhooks'
    ``is_active``/``secret_key`` are never modified.
    """
    with transaction.atomic():
        # Adopting the manifest id lets an app installed before identifiers were
        # recorded (identifier == "") converge; for an app that already has one
        # the mutation guarantees a match, so this is a no-op write.
        app.identifier = manifest_data["id"]
        for manifest_key, attr in MANIFEST_SCALAR_FIELDS:
            setattr(app, attr, manifest_data.get(manifest_key))
        app.save(
            update_fields=["identifier", *(attr for _, attr in MANIFEST_SCALAR_FIELDS)]
        )
        app.permissions.set(manifest_data.get("permissions", []))
        # AppExtension rows have no stable per-row identity, so unchanged
        # extensions are left untouched and only a real change triggers a
        # wholesale rebuild — reissuing extension IDs (which dashboard mounts and
        # URLs reference) on every reload would otherwise break open sessions.
        if _serialize_app_extensions(app) != _serialize_manifest_extensions(
            manifest_data
        ):
            app.extensions.all().delete()
            for extension_data in manifest_data.get("extensions", []):
                _create_app_extension(app, extension_data)
        _resync_app_webhooks(app, manifest_data.get("webhooks", []))

    fetch_brand_data_async(manifest_data, app=app)
    return app
