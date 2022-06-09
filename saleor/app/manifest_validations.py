import logging
from collections import defaultdict
from typing import Dict, Iterable, List

from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat

from ..core.permissions import (
    get_permissions,
    get_permissions_enum_list,
    split_permission_codename,
)
from ..graphql.core.utils import str_to_enum
from ..graphql.webhook.subscription_payload import validate_subscription_query
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .error_codes import AppErrorCode
from .types import AppExtensionMount, AppExtensionTarget
from .validators import AppURLValidator

logger = logging.getLogger(__name__)

T_ERRORS = Dict[str, List[ValidationError]]


def _clean_app_url(url):
    url_validator = AppURLValidator()
    url_validator(url)


def _clean_extension_url_with_only_path(
    manifest_data: dict, target: str, extension_url: str
):
    if target == AppExtensionTarget.APP_PAGE:
        return
    elif manifest_data["appUrl"]:
        _clean_app_url(manifest_data["appUrl"])
    else:
        msg = (
            "Incorrect relation between extension's target and URL fields. "
            "APP_PAGE can be used only with relative URL path."
        )
        logger.warning(msg, extra={"target": target, "url": extension_url})
        raise ValidationError(msg)


def clean_extension_url(extension: dict, manifest_data: dict):
    """Clean assigned extension url.

    Make sure that format of url is correct based on the rest of manifest fields.
    - url can start with '/' when one of these conditions is true:
        a) extension.target == APP_PAGE
        b) appUrl is provided
    - url cannot start with protocol when target == "APP_PAGE"
    """
    extension_url = extension["url"]
    target = extension.get("target") or AppExtensionTarget.POPUP
    if extension_url.startswith("/"):
        _clean_extension_url_with_only_path(manifest_data, target, extension_url)
    elif target == AppExtensionTarget.APP_PAGE:
        msg = "Url cannot start with protocol when target == APP_PAGE"
        logger.warning(msg)
        raise ValidationError(msg)
    else:
        _clean_app_url(extension_url)


def clean_manifest_url(manifest_url):
    try:
        _clean_app_url(manifest_url)
    except (ValidationError, AttributeError):
        msg = "Enter a valid URL."
        code = AppErrorCode.INVALID_URL_FORMAT.value
        raise ValidationError({"manifest_url": ValidationError(msg, code=code)})


def clean_permissions(
    required_permissions: List[str], saleor_permissions: Iterable[Permission]
) -> List[Permission]:
    missing_permissions = []
    all_permissions = {perm[0]: perm[1] for perm in get_permissions_enum_list()}
    for perm in required_permissions:
        if not all_permissions.get(perm):
            missing_permissions.append(perm)
    if missing_permissions:
        error_msg = "Given permissions don't exist."
        code = AppErrorCode.INVALID_PERMISSION.value
        params = {"permissions": missing_permissions}
        raise ValidationError(error_msg, code=code, params=params)

    permissions = [all_permissions[perm] for perm in required_permissions]
    permissions = split_permission_codename(permissions)
    return [p for p in saleor_permissions if p.codename in permissions]


def clean_manifest_data(manifest_data):
    errors: T_ERRORS = defaultdict(list)

    validate_required_fields(manifest_data, errors)
    try:
        _clean_app_url(manifest_data["tokenTargetUrl"])
    except (ValidationError, AttributeError):
        errors["tokenTargetUrl"].append(
            ValidationError(
                "Incorrect format.",
                code=AppErrorCode.INVALID_URL_FORMAT.value,
            )
        )

    saleor_permissions = get_permissions().annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    )
    try:
        app_permissions = clean_permissions(
            manifest_data.get("permissions", []), saleor_permissions
        )
    except ValidationError as e:
        errors["permissions"].append(e)
        app_permissions = []

    manifest_data["permissions"] = app_permissions

    if not errors:
        clean_extensions(manifest_data, app_permissions, errors)
        clean_webhooks(manifest_data, errors)

    if errors:
        raise ValidationError(errors)


def _clean_extension_permissions(extension, app_permissions, errors):
    permissions_data = extension.get("permissions", [])
    try:
        extension_permissions = clean_permissions(permissions_data, app_permissions)
    except ValidationError as e:
        e.params["label"] = extension.get("label")
        errors["extensions"].append(e)
        return

    if len(extension_permissions) != len(permissions_data):
        errors["extensions"].append(
            ValidationError(
                "Extension permission must be listed in App's permissions.",
                code=AppErrorCode.OUT_OF_SCOPE_PERMISSION.value,
            )
        )

    extension["permissions"] = extension_permissions


def clean_extension_enum_field(enum, field_name, extension, errors):
    if extension[field_name] in [code.upper() for code, _ in enum.CHOICES]:
        extension[field_name] = getattr(enum, extension[field_name])
    else:
        errors["extensions"].append(
            ValidationError(
                f"Incorrect value for field: {field_name}",
                code=AppErrorCode.INVALID.value,
            )
        )


def clean_extensions(manifest_data, app_permissions, errors):
    extensions = manifest_data.get("extensions", [])
    for extension in extensions:
        if "target" not in extension:
            extension["target"] = AppExtensionTarget.POPUP
        else:
            clean_extension_enum_field(AppExtensionTarget, "target", extension, errors)
        clean_extension_enum_field(AppExtensionMount, "mount", extension, errors)

        try:
            clean_extension_url(extension, manifest_data)
        except (ValidationError, AttributeError):
            errors["extensions"].append(
                ValidationError(
                    "Incorrect value for field: url.",
                    code=AppErrorCode.INVALID_URL_FORMAT.value,
                )
            )
        _clean_extension_permissions(extension, app_permissions, errors)


def clean_webhooks(manifest_data, errors):
    webhooks = manifest_data.get("webhooks", [])

    async_types = {
        str_to_enum(e_type[0]): e_type[0] for e_type in WebhookEventAsyncType.CHOICES
    }
    sync_types = {
        str_to_enum(e_type[0]): e_type[0] for e_type in WebhookEventSyncType.CHOICES
    }

    target_url_validator = AppURLValidator(
        schemes=["http", "https", "awssqs", "gcpubsub"]
    )

    for webhook in webhooks:
        if not validate_subscription_query(webhook["query"]):
            errors["webhooks"].append(
                ValidationError(
                    "Subscription query is not valid.",
                    code=AppErrorCode.INVALID.value,
                )
            )

        webhook["events"] = []
        for e_type in webhook.get("asyncEvents", []):
            try:
                webhook["events"].append(async_types[e_type])
            except KeyError:
                errors["webhooks"].append(
                    ValidationError(
                        "Invalid asynchronous event.",
                        code=AppErrorCode.INVALID.value,
                    )
                )
        for e_type in webhook.get("syncEvents", []):
            try:
                webhook["events"].append(sync_types[e_type])
            except KeyError:
                errors["webhooks"].append(
                    ValidationError(
                        "Invalid synchronous event.",
                        code=AppErrorCode.INVALID.value,
                    )
                )

        try:
            target_url_validator(webhook["targetUrl"])
        except ValidationError:
            errors["webhooks"].append(
                ValidationError(
                    "Invalid target url.",
                    code=AppErrorCode.INVALID_URL_FORMAT.value,
                )
            )


def validate_required_fields(manifest_data, errors):
    manifest_required_fields = {"id", "version", "name", "tokenTargetUrl"}
    extension_required_fields = {"label", "url", "mount"}
    webhook_required_fields = {"name", "targetUrl", "query"}

    if manifest_missing_fields := manifest_required_fields.difference(manifest_data):
        for missing_field in manifest_missing_fields:
            errors[missing_field].append(
                ValidationError("Field required.", code=AppErrorCode.REQUIRED.value)
            )

    app_extensions_data = manifest_data.get("extensions", [])
    for extension in app_extensions_data:
        extension_fields = set(extension.keys())
        if missing_fields := extension_required_fields.difference(extension_fields):
            errors["extensions"].append(
                ValidationError(
                    "Missing required fields for app extension: %s."
                    % ", ".join(missing_fields),
                    code=AppErrorCode.REQUIRED.value,
                )
            )

    webhooks = manifest_data.get("webhooks", [])
    for webhook in webhooks:
        webhook_fields = set(webhook.keys())
        if missing_fields := webhook_required_fields.difference(webhook_fields):
            errors["webhooks"].append(
                ValidationError(
                    "Missing required fields for webhook: %s."
                    % ", ".join(missing_fields),
                    code=AppErrorCode.REQUIRED.value,
                )
            )
