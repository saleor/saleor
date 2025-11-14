import logging
from collections import defaultdict
from collections.abc import Iterable

from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat
from semantic_version import NpmSpec, Version
from semantic_version.base import Range

from .. import __version__
from ..giftcard.const import GIFT_CARD_PAYMENT_GATEWAY_ID
from ..graphql.core.utils import str_to_enum
from ..graphql.webhook.subscription_query import SubscriptionQuery
from ..permission.enums import (
    get_permissions,
    get_permissions_enum_list,
    split_permission_codename,
)
from ..permission.models import Permission
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..webhook.validators import custom_headers_validator
from .error_codes import AppErrorCode
from .models import App
from .types import DEFAULT_APP_TARGET
from .validators import AppURLValidator, brand_validator

logger = logging.getLogger(__name__)

T_ERRORS = dict[str, list[ValidationError]]


class RequiredSaleorVersionSpec(NpmSpec):
    class Parser(NpmSpec.Parser):
        @classmethod
        def range(cls, operator, target):
            # change prerelease policy from `same-patch` to `natural`
            return Range(operator, target, prerelease_policy=Range.PRERELEASE_NATURAL)


def _clean_app_url(url):
    url_validator = AppURLValidator()
    url_validator(url)


def _clean_extension_url(extension: dict, manifest_data: dict):
    """Clean assigned extension url.

    Make sure that format of url is correct based on the rest of manifest fields.
    - url can start with '/' when one of these conditions is true:
        a) extension.target == APP_PAGE
        b) appUrl is provided
    - url cannot start with protocol when target == "APP_PAGE"
    """
    extension_url = extension["url"]

    # Assume app URL is the one that originally received the token.
    app_url = manifest_data.get("tokenTargetUrl")

    if not app_url:
        raise ValidationError("Manifest is invalid, token_target_url is missing")

    # Only validate absolute URLs (with protocol)
    # Relative URLs (starting with '/') are allowed when tokenTargetUrl is provided
    if not extension_url.startswith("/"):
        _clean_app_url(extension_url)


def clean_manifest_url(manifest_url):
    try:
        _clean_app_url(manifest_url)
    except (ValidationError, AttributeError) as e:
        msg = "Enter a valid URL."
        code = AppErrorCode.INVALID_URL_FORMAT.value
        raise ValidationError({"manifest_url": ValidationError(msg, code=code)}) from e


def _clean_permissions(
    required_permissions: list[str], saleor_permissions: Iterable[Permission]
) -> list[Permission]:
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


def clean_manifest_data(manifest_data, raise_for_saleor_version=False):
    errors: T_ERRORS = defaultdict(list)

    _validate_required_fields(manifest_data, errors)

    try:
        if "tokenTargetUrl" in manifest_data:
            _clean_app_url(manifest_data["tokenTargetUrl"])
    except (ValidationError, AttributeError):
        errors["tokenTargetUrl"].append(
            ValidationError(
                "Incorrect format.",
                code=AppErrorCode.INVALID_URL_FORMAT.value,
            )
        )

    try:
        manifest_data["requiredSaleorVersion"] = _clean_required_saleor_version(
            manifest_data.get("requiredSaleorVersion"), raise_for_saleor_version
        )
    except ValidationError as e:
        errors["requiredSaleorVersion"].append(e)

    try:
        manifest_data["author"] = _clean_author(manifest_data.get("author"))
    except ValidationError as e:
        errors["author"].append(e)

    try:
        brand_validator(manifest_data.get("brand"))
    except ValidationError as e:
        errors["brand"].append(e)

    saleor_permissions = get_permissions().annotate(
        formatted_codename=Concat("content_type__app_label", Value("."), "codename")
    )
    try:
        app_permissions = _clean_permissions(
            manifest_data.get("permissions", []), saleor_permissions
        )
    except ValidationError as e:
        errors["permissions"].append(e)
        app_permissions = []

    manifest_data["permissions"] = app_permissions
    if (
        app := App.objects.not_removed()
        .filter(identifier=manifest_data.get("id"))
        .first()
    ):
        errors["identifier"].append(
            ValidationError(
                f"App with the same identifier is already installed: {app.name}",
                code=AppErrorCode.UNIQUE.value,
            )
        )

    if manifest_data.get("id") == GIFT_CARD_PAYMENT_GATEWAY_ID:
        errors["identifier"].append(
            ValidationError(
                "App with this identifier cannot be installed",
                code=AppErrorCode.UNIQUE.value,
            )
        )

    if not errors:
        _clean_extensions(manifest_data, app_permissions, errors)
        _clean_webhooks(manifest_data, errors)

    if errors:
        raise ValidationError(errors)


def _clean_extension_permissions(extension, app_permissions, errors):
    permissions_data = extension.get("permissions", [])
    try:
        extension_permissions = _clean_permissions(permissions_data, app_permissions)
    except ValidationError as e:
        if e.params is None:
            e.params = {}
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


def _clean_extensions(manifest_data, app_permissions, errors):
    extensions = manifest_data.get("extensions", [])

    for extension in extensions:
        if "target" not in extension:
            extension["target"] = DEFAULT_APP_TARGET

        # Save in lowercase to maintain backwards compatibility with enums, that were used previously
        extension["target"] = extension["target"].lower()
        extension["mount"] = extension["mount"].lower()

        try:
            _clean_extension_url(extension, manifest_data)
        except (ValidationError, AttributeError):
            errors["extensions"].append(
                ValidationError(
                    "Incorrect value for field: url.",
                    code=AppErrorCode.INVALID_URL_FORMAT.value,
                )
            )

        _clean_extension_permissions(extension, app_permissions, errors)


def _clean_webhooks(manifest_data, errors):
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
        webhook["isActive"] = webhook.get("isActive", True)
        if not isinstance(webhook["isActive"], bool):
            errors["webhooks"].append(
                ValidationError(
                    "Incorrect value for field: isActive.",
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

        subscription_query = SubscriptionQuery(webhook["query"])
        if not subscription_query.is_valid:
            errors["webhooks"].append(
                ValidationError(
                    "Subscription query is not valid: " + subscription_query.error_msg,
                    code=AppErrorCode.INVALID.value,
                )
            )

        if not webhook["events"]:
            webhook["events"] = subscription_query.events

        try:
            target_url_validator(webhook["targetUrl"])
        except ValidationError:
            errors["webhooks"].append(
                ValidationError(
                    "Invalid target url.",
                    code=AppErrorCode.INVALID_URL_FORMAT.value,
                )
            )

        if custom_headers := webhook.get("customHeaders"):
            try:
                webhook["customHeaders"] = custom_headers_validator(custom_headers)
            except ValidationError as err:
                errors["webhooks"].append(
                    ValidationError(
                        f"Invalid custom headers: {err.message}",
                        code=AppErrorCode.INVALID_CUSTOM_HEADERS.value,
                    )
                )


def _validate_required_fields(manifest_data, errors):
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
                    "Missing required fields for app extension: "
                    f"{', '.join(missing_fields)}.",
                    code=AppErrorCode.REQUIRED.value,
                )
            )

    webhooks = manifest_data.get("webhooks", [])
    for webhook in webhooks:
        webhook_fields = set(webhook.keys())
        if missing_fields := webhook_required_fields.difference(webhook_fields):
            errors["webhooks"].append(
                ValidationError(
                    f"Missing required fields for webhook: "
                    f"{', '.join(missing_fields)}.",
                    code=AppErrorCode.REQUIRED.value,
                )
            )


def _parse_version(version_str: str) -> Version:
    return Version(version_str)


def _clean_required_saleor_version(
    required_version,
    raise_for_saleor_version: bool,
    saleor_version=__version__,
) -> dict | None:
    if not required_version:
        return None
    try:
        spec = RequiredSaleorVersionSpec(required_version)
    except Exception as e:
        msg = "Incorrect value for required Saleor version."
        raise ValidationError(msg, code=AppErrorCode.INVALID.value) from e
    version = _parse_version(saleor_version)
    satisfied = spec.match(version)
    if raise_for_saleor_version and not satisfied:
        msg = f"Saleor version {saleor_version} is not supported by the app."
        raise ValidationError(msg, code=AppErrorCode.UNSUPPORTED_SALEOR_VERSION.value)
    return {"constraint": required_version, "satisfied": satisfied}


def _clean_author(author) -> str | None:
    if author is None:
        return None
    if isinstance(author, str):
        if clean := author.strip():
            return clean
    raise ValidationError(
        "Incorrect value for field: author", code=AppErrorCode.INVALID.value
    )
