from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Value
from django.db.models.functions import Concat
from pydantic import AnyHttpUrl, AnyUrl, ConstrainedStr, ValidationError, validator
from semantic_version import NpmSpec, Version
from semantic_version.base import Range

from .. import __version__
from ..core.schema import (
    BaseChoice,
    Error,
    SaleorValueError,
    Schema,
    ValidationErrorConfig,
    translate_validation_error,
)
from ..graphql.webhook.subscription_query import SubscriptionQuery
from ..permission.enums import get_permissions_enum_list, get_permissions_from_names
from ..permission.models import Permission
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..webhook.validators import custom_headers_validator
from .error_codes import AppErrorCode
from .types import AppExtensionMount, AppExtensionTarget


class RequiredSaleorVersionSpec(NpmSpec):
    class Parser(NpmSpec.Parser):
        @classmethod
        def range(cls, operator, target):
            # change prerelease policy from `same-patch` to `natural`
            return Range(operator, target, prerelease_policy=Range.PRERELEASE_NATURAL)


if TYPE_CHECKING:
    PermissionType = Permission
    SubscriptionQueryStr = SubscriptionQuery
    AppExtensionTargets = str
else:
    PermissionType = Enum(
        value="PermissionType",
        names=[(name, name) for name, _ in get_permissions_enum_list()],
    )
    SubscriptionQueryStr = str

    class AppExtensionTargets(BaseChoice):
        _CHOICES = {target.upper(): target for target, _ in AppExtensionTarget.CHOICES}


class AppExtensionMountChoice(BaseChoice):
    _CHOICES = {mount.upper(): mount for mount, _ in AppExtensionMount.CHOICES}


class AsyncEventTypes(BaseChoice):
    _CHOICES = {event.upper(): event for event, _ in WebhookEventAsyncType.CHOICES}


class SyncEventTypes(BaseChoice):
    _CHOICES = {event.upper(): event for event, _ in WebhookEventSyncType.CHOICES}


class AppExtensionMounts(BaseChoice):
    _CHOICES = {mount.upper(): mount for mount, _ in AppExtensionMount.CHOICES}


class WebhookTargetUrl(AnyUrl):
    allowed_schemes = {"http", "https", "awssqs", "gcpubsub"}
    tld_required = False


class Webhook(Schema):
    name: str
    is_active: bool = True
    target_url: WebhookTargetUrl
    query: SubscriptionQueryStr
    async_events: list[AsyncEventTypes] = []
    sync_events: list[SyncEventTypes] = []
    custom_headers: Optional[Dict[str, str]] = None
    events: list[str] = []

    class Config(ValidationErrorConfig):
        errors_map = {
            "async_events": Error(msg_tmp="Invalid asynchronous event."),
            "sync_events": Error(msg_tmp="Invalid synchronous event."),
            "target_url": Error(msg_tmp="Invalid target url."),
            "custom_headers": Error(code=AppErrorCode.INVALID_CUSTOM_HEADERS),
        }

    @validator("query")
    def validate_query(cls, v: str):
        subscription_query = SubscriptionQuery(v)
        if not subscription_query.is_valid:
            raise SaleorValueError(
                "Subscription query is not valid: " + subscription_query.error_msg,
                code=AppErrorCode.INVALID.value,
            )
        return subscription_query

    @validator("async_events", "sync_events", each_item=True)
    def lower_events(cls, v: str):
        return v.lower()

    @validator("events", always=True)
    def gather_events(cls, _, values, **kwargs):
        events = values["async_events"] + values["sync_events"]
        if not events:
            events = values["query"].events
        return events

    @validator("custom_headers")
    def validate_headers(cls, v):
        if v is not None:
            try:
                return custom_headers_validator(v)
            except DjangoValidationError as err:
                raise SaleorValueError(
                    f"Invalid custom headers: {err.message}",
                    code=AppErrorCode.INVALID_CUSTOM_HEADERS.value,
                )


def validate_permissions(value: list[str]) -> List[Permission]:
    return list(
        get_permissions_from_names(value).annotate(
            formated_codename=Concat("content_type__app_label", Value("."), "codename")
        )
    )


class UrlPathStr(ConstrainedStr):
    regex = r"(/[^\s?#]*)(\?[^\s#]*)?(#[^\s#]*)?"


class Extension(Schema):
    label: str
    target: AppExtensionTargets = AppExtensionTarget.POPUP
    mount: AppExtensionMounts
    url: Union[AnyHttpUrl, UrlPathStr]
    permissions: List[PermissionType] = []

    class Config:
        errors_map = {
            "permissions": Error(
                code=AppErrorCode.INVALID_PERMISSION,
                msg_tmp="Given permissions don't exist.",
            ),
            "url": Error(code=AppErrorCode.INVALID_URL_FORMAT),
        }

    @validator("target", "mount")
    def lower(cls, v: str):
        return v.lower()

    @validator("url")
    def validate_url(cls, v, values, **kwargs):
        if isinstance(v, AnyHttpUrl):
            if values.get("target") == AppExtensionTarget.APP_PAGE:
                msg = "Url cannot start with protocol when target == APP_PAGE"
                raise SaleorValueError(msg, code=AppErrorCode.INVALID_URL_FORMAT.value)
        return v

    _val_permissions = validator("permissions", allow_reuse=True)(validate_permissions)


class RequiredSaleorVersion(Schema):
    constraint: str
    satisfied: bool


def parse_version(version_str: str) -> Version:
    return Version(version_str)


class AuthorStr(ConstrainedStr):
    strip_whitespace = True
    min_length = 1


class Manifest(Schema):
    id: str
    version: str
    name: str
    about: str
    token_target_url: AnyHttpUrl
    required_saleor_version: Optional[RequiredSaleorVersion] = None
    author: Optional[AuthorStr] = None
    permissions: list[PermissionType] = []

    app_url: Optional[AnyHttpUrl] = None
    configuration_url: Optional[AnyHttpUrl] = None
    data_privacy: str
    data_privacy_url: Optional[AnyHttpUrl] = None
    homepage_url: Optional[AnyHttpUrl] = None
    support_url: Optional[AnyHttpUrl] = None
    audience: Optional[str] = None

    webhooks: list[Webhook] = []
    extensions: list[Extension] = []

    class Config(ValidationErrorConfig):
        default_error = Error(code=AppErrorCode.INVALID)
        errors_types_map = {
            "value_error.missing": Error(
                code=AppErrorCode.REQUIRED, msg_tmp="Field required."
            ),
            "value_error.url": Error(
                code=AppErrorCode.INVALID_URL_FORMAT, msg_tmp="Incorrect format."
            ),
        }
        errors_map = {
            "permissions": Error(
                code=AppErrorCode.INVALID_PERMISSION,
                msg_tmp="Given permissions don't exist.",
            )
        }

    # validators
    _val_permissions = validator("permissions", allow_reuse=True)(validate_permissions)

    @validator("extensions", each_item=True)
    def validate_extension(cls, v: Extension, values, **kwargs):
        if isinstance(v.url, UrlPathStr):
            if v.target == AppExtensionTarget.APP_PAGE:
                return v
            elif values["app_url"] is None:
                raise ValueError("Incorrect value for field: url.")
            msg = (
                "Incorrect relation between extension's target and URL fields. "
                "APP_PAGE can be used only with relative URL path."
            )
            raise ValueError(msg)
        return v

    @validator("extensions")
    def validate_extension_permission(cls, v: List[Extension], values, **kwargs):
        app_permissions = values.get("permissions", [])
        for extension in v:
            for permission in extension.permissions:
                if permission not in app_permissions:
                    raise SaleorValueError(
                        "Extension permission must be listed in App's permissions.",
                        code=AppErrorCode.OUT_OF_SCOPE_PERMISSION.value,
                    )
        return v

    @validator("required_saleor_version", pre=True)
    def validate_required_version(cls, v):
        if v is None:
            return v
        try:
            spec = RequiredSaleorVersionSpec(v)
        except Exception:
            msg = "Incorrect value for required Saleor version."
            raise ValueError(msg)
        version = parse_version(__version__)
        return RequiredSaleorVersion(constraint=v, satisfied=spec.match(version))


def clean_manifest_data(manifest_data, raise_for_saleor_version=False):
    try:
        m = Manifest.parse_obj(manifest_data)
        if raise_for_saleor_version and m.required_saleor_version:
            if not m.required_saleor_version.satisfied:
                msg = f"Saleor version {__version__} is not supported by the app."
                raise DjangoValidationError(
                    {
                        "requiredSaleorVersion": DjangoValidationError(
                            msg, code=AppErrorCode.UNSUPPORTED_SALEOR_VERSION.value
                        )
                    }
                )
        return m.dict(by_alias=True)
    except ValidationError as error:
        raise translate_validation_error(error)
