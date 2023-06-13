from enum import Enum
from typing import TYPE_CHECKING, Optional, Union, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import Field, constr, stricturl, validator
from semantic_version import NpmSpec, Version
from semantic_version.base import Range

from .. import __version__
from ..core.json_schema import (
    CustomValueError,
    ErrorConversionConfig,
    ErrorConversionModel,
    ErrorOverride,
    StrFieldMixin,
)
from ..graphql.webhook.subscription_query import (
    SubscriptionQuery as SubscriptionQueryBase,
)
from ..permission.enums import get_permissions_enum_list
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..webhook.validators import custom_headers_validator
from .error_codes import AppErrorCode
from .types import AppExtensionMount, AppExtensionTarget

SALEOR_VERSION = Version(__version__)

if TYPE_CHECKING:
    AuthorStr = str
    UrlPathStr = str
    AnyHttpUrl = str
    WebhookTargetUrl = str
else:
    AuthorStr = constr(strip_whitespace=True, min_length=1, max_length=60)
    UrlPathStr = constr(regex=r"(/[^\s?#]*)(\?[^\s#]*)?(#[^\s#]*)?")
    AnyHttpUrl = stricturl(
        tld_required=False, max_length=200, allowed_schemes={"http", "https"}
    )
    WebhookTargetUrl = stricturl(
        tld_required=False,
        max_length=255,
        allowed_schemes={"http", "https", "awssqs", "gcpubsub"},
    )


class RequiredSaleorVersionSpec(NpmSpec, StrFieldMixin):
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
            raise CustomValueError(
                "Invalid value. Version range required in the semver format."
            )
        if cls.raise_for_version:
            if not spec.satisfied:
                raise CustomValueError(
                    f"Saleor version {SALEOR_VERSION} is not supported by the app.",
                    error_code=AppErrorCode.UNSUPPORTED_SALEOR_VERSION,
                )
        return spec

    @property
    def constraint(self) -> str:
        return str(self)

    @property
    def satisfied(self) -> bool:
        return self.match(SALEOR_VERSION)


class SubscriptionQuery(SubscriptionQueryBase, StrFieldMixin):
    @classmethod
    def validate(cls, value: str):
        query = SubscriptionQuery(value)
        if not query.is_valid:
            raise CustomValueError(query.error_msg)
        return query


Permission = Enum(  # type: ignore[misc]
    "Permission", [(p, p) for p, _ in get_permissions_enum_list()]
)
AppExtensionTargetEnum = Enum(  # type: ignore[misc]
    "AppExtensionTargetEnum", [(m, m.upper()) for m, _ in AppExtensionTarget.CHOICES]
)
AppExtensionTargetEnum.__doc__ = AppExtensionTarget.__doc__
AppExtensionMountEnum = Enum(  # type: ignore[misc]
    "AppExtensionMountEnum", [(m, m.upper()) for m, _ in AppExtensionMount.CHOICES]
)
AppExtensionMountEnum.__doc__ = AppExtensionMount.__doc__
WebhookEventTypeAsyncEnum = Enum(  # type: ignore[misc]
    "WebhookEventTypeAsyncEnum",
    [(m, m.upper()) for m, _ in WebhookEventAsyncType.CHOICES],
)
WebhookEventTypeAsyncEnum.__doc__ = (
    "The asynchronous events that webhook wants to subscribe."
)
WebhookEventTypeSyncEnum = Enum(  # type: ignore[misc]
    "WebhookEventTypeSyncEnum",
    [(m, m.upper()) for m, _ in WebhookEventSyncType.CHOICES],
)
WebhookEventTypeSyncEnum.__doc__ = (
    "The synchronous events that webhook wants to subscribe."
)

URL_ERROR_OVERRIDE: ErrorOverride = {"code": AppErrorCode.INVALID_URL_FORMAT}
PERMISSION_ERROR_OVERRIDE: ErrorOverride = {
    "code": AppErrorCode.INVALID_PERMISSION,
    "msg": "Given permission doesn't exist.",
}


class Webhook(ErrorConversionModel):
    name: str = Field(max_length=255)
    is_active: bool = True
    target_url: WebhookTargetUrl
    query: SubscriptionQuery
    async_events: list[WebhookEventTypeAsyncEnum] = []
    sync_events: list[WebhookEventTypeSyncEnum] = []
    custom_headers: dict[str, str] = {}

    class Config(ErrorConversionConfig):
        field_error_overrides = {"target_url": URL_ERROR_OVERRIDE}

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
            raise CustomValueError(cast(str, err.message), error_code=code)


class Extension(ErrorConversionModel):
    label: str = Field(max_length=256)
    target: AppExtensionTargetEnum = AppExtensionTargetEnum[AppExtensionTarget.POPUP]
    mount: AppExtensionMountEnum
    url: Union[AnyHttpUrl, UrlPathStr]
    permissions: list[Permission] = []

    class Config(ErrorConversionConfig):
        field_error_overrides = {
            "permissions": PERMISSION_ERROR_OVERRIDE,
            "url": URL_ERROR_OVERRIDE,
        }

    @validator("url")
    def validate_url(cls, v: str, values, **kwargs):
        target = cast(AppExtensionTargetEnum, values.get("target"))
        if (
            not v.startswith("/")
            and target == AppExtensionTargetEnum[AppExtensionTarget.APP_PAGE]
        ):
            msg = "Url cannot start with protocol when target == APP_PAGE"
            raise CustomValueError(msg)
        return v


class ManifestBrandLogo(ErrorConversionModel):
    default: AnyHttpUrl

    class Config(ErrorConversionConfig):
        field_error_overrides = {"default": URL_ERROR_OVERRIDE}


class ManifestBrandData(ErrorConversionModel):
    logo: ManifestBrandLogo


class Manifest(ErrorConversionModel):
    id: str = Field(
        max_length=256, description="Id of application used internally by Saleor"
    )
    version: str = Field(max_length=60, description="App version")
    name: str = Field(max_length=60, description="App name displayed in the dashboard")
    token_target_url: AnyHttpUrl = Field(
        description="Endpoint used during process of app installation"
    )
    about: Optional[str] = Field(
        None, description="Description of the app displayed in the dashboard"
    )
    required_saleor_version: Optional[RequiredSaleorVersionSpec] = Field(
        None,
        description="Version range, in the semver format, which specifies Saleor "
        "version required by the app. The field will be respected starting from "
        "Saleor 3.13",
    )
    author: Optional[AuthorStr] = Field(
        None,
        description="App author name displayed in the dashboard "
        "(starting from Saleor 3.13)",
    )
    app_url: Optional[AnyHttpUrl] = Field(
        None, description="App website rendered in the dashboard"
    )
    configuration_url: Optional[AnyHttpUrl] = Field(
        None,
        description="Address to the app configuration page, which is rendered in "
        "the dashboard (deprecated in Saleor 3.5, use appUrl instead)",
        deprecated=True,
    )
    data_privacy: Optional[str] = Field(
        None,
        description="Short description of privacy policy displayed in the "
        "dashboard (deprecated in Saleor 3.5, use dataPrivacyUrl instead)",
        deprecated=True,
    )
    data_privacy_url: Optional[AnyHttpUrl] = Field(
        None, description="URL to the full privacy policy"
    )
    homepage_url: Optional[AnyHttpUrl] = Field(
        None, description="External URL to the app homepage"
    )
    support_url: Optional[AnyHttpUrl] = Field(
        None, description="External URL to the page where " "app users can find support"
    )
    audience: Optional[str] = Field(None, max_length=256)
    permissions: list[Permission] = Field(
        [], description="Array of permissions requested by the app"
    )
    webhooks: list[Webhook] = Field([], description="List of webhooks that will be set")
    extensions: list[Extension] = Field(
        [], description="List of extensions that will be mounted in Saleor's dashboard"
    )
    brand: Optional[ManifestBrandData] = None

    class Config(ErrorConversionConfig):
        default_error_override = {"code": AppErrorCode.INVALID}
        root_error_override = {
            "code": AppErrorCode.INVALID_MANIFEST_FORMAT,
            "msg": "Incorrect structure of manifest.",
        }
        error_type_overrides = {
            "value_error.missing": {
                "code": AppErrorCode.REQUIRED,
                "msg": "Field required.",
            },
            "value_error.url*": {"code": AppErrorCode.INVALID_URL_FORMAT},
        }
        field_error_overrides = {
            "permissions": PERMISSION_ERROR_OVERRIDE,
            "token_target_url": URL_ERROR_OVERRIDE,
            "app_url": URL_ERROR_OVERRIDE,
            "configuration_url": URL_ERROR_OVERRIDE,
            "data_privacy_url": URL_ERROR_OVERRIDE,
            "homepage_url": URL_ERROR_OVERRIDE,
            "support_url": URL_ERROR_OVERRIDE,
        }

    @validator("extensions", each_item=True)
    def validate_extension(cls, v: Extension, values, **kwargs):
        app_permissions = values.get("permissions", [])
        for permission in v.permissions:
            if permission not in app_permissions:
                raise CustomValueError(
                    "Extension permission must be listed in App's permissions.",
                    error_code=AppErrorCode.OUT_OF_SCOPE_PERMISSION,
                )
        app_url = values.get("app_url", [])
        if (
            v.url.startswith("/")
            and v.target != AppExtensionTargetEnum[AppExtensionTarget.APP_PAGE]
            and not app_url
        ):
            msg = (
                "Incorrect relation between extension's target and URL fields. "
                "APP_PAGE can be used only with relative URL path."
            )
            raise CustomValueError(msg, error_code=AppErrorCode.INVALID_URL_FORMAT)
        return v


class StrictRequiredSaleorVersionSpec(RequiredSaleorVersionSpec):
    raise_for_version = True


class StrictManifest(Manifest):
    required_saleor_version: Optional[StrictRequiredSaleorVersionSpec] = None
