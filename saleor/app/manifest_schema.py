import re
from enum import Enum
from typing import Annotated, Any, Dict, Optional, Union, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import AnyUrl, ConstrainedStr, Field, validator
from pydantic.errors import MissingError, UrlError
from semantic_version import NpmSpec, Version
from semantic_version.base import Range

from .. import __version__
from ..core.schema import SaleorValidationError, Schema, ValidationErrorConfig
from ..graphql.webhook.subscription_query import (
    SubscriptionQuery as SubscriptionQueryBase,
)
from ..permission.enums import get_permissions_enum_list
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..webhook.validators import custom_headers_validator
from .error_codes import AppErrorCode
from .manifest_schema_extras import manifest_fields_schema_extra
from .types import AppExtensionMount, AppExtensionTarget

SALEOR_VERSION = Version(__version__)


class RequiredSaleorVersionSpec(NpmSpec, ConstrainedStr):
    raise_for_version = False

    class Parser(NpmSpec.Parser):
        @classmethod
        def range(cls, operator, target):
            # change prerelease policy from `same-patch` to `natural`
            return Range(operator, target, prerelease_policy=Range.PRERELEASE_NATURAL)

    @classmethod
    def validate(cls, value: str):
        try:
            spec = cls(value)
        except Exception:
            raise SaleorValidationError(
                msg="Invalid value. Version range required in the semver format."
            )
        if cls.raise_for_version:
            if not spec.satisfied:
                raise SaleorValidationError(
                    msg=f"Saleor version {SALEOR_VERSION} is not supported by the app.",
                    code=AppErrorCode.UNSUPPORTED_SALEOR_VERSION,
                )
        return spec

    @property
    def constraint(self) -> str:
        return str(self)

    @property
    def satisfied(self) -> bool:
        return self.match(SALEOR_VERSION)


class SubscriptionQuery(SubscriptionQueryBase, ConstrainedStr):
    @classmethod
    def validate(cls, value: str):
        query = SubscriptionQuery(value)
        if not query.is_valid:
            raise SaleorValidationError(msg=query.error_msg)
        return query


PermissionChoice = Enum(  # type: ignore[misc]
    "PermissionChoice", [(p, p) for p, _ in get_permissions_enum_list()]
)

AppExtensionTargets = Enum(  # type: ignore[misc]
    "AppExtensionTargets", [(m, m.upper()) for m, _ in AppExtensionTarget.CHOICES]
)

AppExtensionMounts = Enum(  # type: ignore[misc]
    "AppExtensionMounts", [(m, m.upper()) for m, _ in AppExtensionMount.CHOICES]
)

AsyncEventTypes = Enum(  # type: ignore[misc]
    "AsyncEventTypes", [(m, m.upper()) for m, _ in WebhookEventAsyncType.CHOICES]
)

SyncEventTypes = Enum(  # type: ignore[misc]
    "SyncEventTypes", [(m, m.upper()) for m, _ in WebhookEventSyncType.CHOICES]
)


class AnyHttpUrl(AnyUrl):
    allowed_schemes = {"http", "https"}
    max_length = 200

    @classmethod
    def validate(cls, value, field, config):
        try:
            return super().validate(value, field, config)
        except (ValueError, TypeError) as error:
            raise SaleorValidationError(
                str(error), code=AppErrorCode.INVALID_URL_FORMAT
            )


class WebhookTargetUrl(AnyHttpUrl):
    allowed_schemes = {"http", "https", "awssqs", "gcpubsub"}
    tld_required = False
    max_length = 255


class Webhook(Schema):
    name: Annotated[str, Field(max_length=255)]
    is_active: bool = True
    target_url: WebhookTargetUrl
    query: SubscriptionQuery
    async_events: list[AsyncEventTypes] = []
    sync_events: list[SyncEventTypes] = []
    custom_headers: Dict[str, str] = {}

    @property
    def events(self) -> list[str]:
        events_list = [event.name for event in (self.async_events + self.sync_events)]
        return events_list or self.query.events

    @validator("custom_headers")
    def validate_headers(cls, v):
        try:
            return custom_headers_validator(v)
        except DjangoValidationError as err:
            code = AppErrorCode.INVALID_CUSTOM_HEADERS
            raise SaleorValidationError(msg=cast(str, err.message), code=code)


class UrlPathStr(ConstrainedStr):
    regex = r"(/[^\s?#]*)(\?[^\s#]*)?(#[^\s#]*)?"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> str:
        if isinstance(value, str):
            if cls.max_length is None or len(value) <= cls.max_length:
                if re.match(cls.regex, value):
                    return value
        raise SaleorValidationError(
            msg="Invalid URL path.", code=AppErrorCode.INVALID_URL_FORMAT
        )


class Extension(Schema):
    label: Annotated[str, Field(max_length=256)]
    target: AppExtensionTargets = AppExtensionTargets[AppExtensionTarget.POPUP]
    mount: AppExtensionMounts
    url: Union[AnyHttpUrl, UrlPathStr]
    permissions: list[PermissionChoice] = []

    class Config(ValidationErrorConfig):
        field_errors_map = {
            "permissions": {
                "code": AppErrorCode.INVALID_PERMISSION,
                "msg": "Given permission don't exist.",
            }
        }

    @validator("url")
    def validate_url(cls, v: str, values, **kwargs):
        target = cast(AppExtensionTargets, values.get("target"))
        if (
            not v.startswith("/")
            and target == AppExtensionTargets[AppExtensionTarget.APP_PAGE]
        ):
            msg = "Url cannot start with protocol when target == APP_PAGE"
            raise SaleorValidationError(msg, code=AppErrorCode.INVALID_URL_FORMAT)
        return v


class AuthorStr(ConstrainedStr):
    strip_whitespace = True
    min_length = 1
    max_length = 60


class Manifest(Schema):
    id: Annotated[str, Field(max_length=256)]
    version: Annotated[str, Field(max_length=60)]
    name: Annotated[str, Field(max_length=60)]
    token_target_url: AnyHttpUrl
    about: Optional[str] = None
    required_saleor_version: Optional[RequiredSaleorVersionSpec] = None
    author: Optional[AuthorStr] = None
    app_url: Optional[AnyHttpUrl] = None
    configuration_url: Optional[AnyHttpUrl] = None
    data_privacy: Optional[str] = None
    data_privacy_url: Optional[AnyHttpUrl] = None
    homepage_url: Optional[AnyHttpUrl] = None
    support_url: Optional[AnyHttpUrl] = None
    audience: Annotated[Optional[str], Field(max_length=256)] = None
    permissions: list[PermissionChoice] = []
    webhooks: list[Webhook] = []
    extensions: list[Extension] = []

    class Config(ValidationErrorConfig):
        default_error = {"code": AppErrorCode.INVALID}
        errors_map = {
            MissingError: {"code": AppErrorCode.REQUIRED, "msg": "Field required."},
            UrlError: {"code": AppErrorCode.INVALID_URL_FORMAT},
        }
        field_errors_map = {
            "permissions": {
                "code": AppErrorCode.INVALID_PERMISSION,
                "msg": "Given permission don't exist.",
            }
        }
        fields = manifest_fields_schema_extra

    @validator("extensions", each_item=True)
    def validate_extension(cls, v: Extension, values, **kwargs):
        app_permissions = values.get("permissions", [])
        for permission in v.permissions:
            if permission not in app_permissions:
                raise SaleorValidationError(
                    msg="Extension permission must be listed in App's permissions.",
                    code=AppErrorCode.OUT_OF_SCOPE_PERMISSION,
                )
        app_url = values.get("app_url", [])
        if (
            v.url.startswith("/")
            and v.target != AppExtensionTargets[AppExtensionTarget.APP_PAGE]
            and not app_url
        ):
            msg = (
                "Incorrect relation between extension's target and URL fields. "
                "APP_PAGE can be used only with relative URL path."
            )
            raise SaleorValidationError(msg, code=AppErrorCode.INVALID_URL_FORMAT)
        return v


class RequiredSaleorVersionStrictSpec(RequiredSaleorVersionSpec):
    raise_for_version = True


class ManifestStrict(Manifest):
    required_saleor_version: Optional[RequiredSaleorVersionStrictSpec] = None
