from enum import Enum
from typing import Annotated, Dict, Optional, Union, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import AnyUrl, ConstrainedStr, Field, validator
from pydantic.errors import (
    AnyStrMaxLengthError,
    AnyStrMinLengthError,
    MissingError,
    StrRegexError,
    UrlError,
)
from semantic_version import NpmSpec, Version
from semantic_version.base import Range

from .. import __version__
from ..core.json_schema import (
    FIELD_MAPPING_TYPE,
    SaleorValidationError,
    ValidationErrorConfig,
    ValidationErrorSchema,
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

URL_ERROR_MAPPING: FIELD_MAPPING_TYPE = [
    (
        (AnyStrMinLengthError, AnyStrMaxLengthError),
        {"code": AppErrorCode.INVALID_URL_FORMAT},
    )
]
PERMISSION_ERROR_MAPPING: FIELD_MAPPING_TYPE = [
    (
        Exception,
        {
            "code": AppErrorCode.INVALID_PERMISSION,
            "msg": "Given permission don't exist.",
        },
    )
]


class AnyHttpUrl(AnyUrl):
    allowed_schemes = {"http", "https"}
    max_length = 200


class WebhookTargetUrl(AnyHttpUrl):
    allowed_schemes = {"http", "https", "awssqs", "gcpubsub"}
    tld_required = False
    max_length = 255


class Webhook(ValidationErrorSchema):
    name: Annotated[str, Field(max_length=255)]
    is_active: bool = True
    target_url: WebhookTargetUrl
    query: SubscriptionQuery
    async_events: list[WebhookEventTypeAsyncEnum] = []
    sync_events: list[WebhookEventTypeSyncEnum] = []
    custom_headers: Dict[str, str] = {}

    class Config(ValidationErrorConfig):
        field_errors_map = {"target_url": URL_ERROR_MAPPING}

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


URL_PATH_ERROR_MAPPING: FIELD_MAPPING_TYPE = [
    (
        StrRegexError,
        {"code": AppErrorCode.INVALID_URL_FORMAT, "msg": "Invalid URL path."},
    )
]


class Extension(ValidationErrorSchema):
    label: Annotated[str, Field(max_length=256)]
    target: AppExtensionTargetEnum = AppExtensionTargetEnum[AppExtensionTarget.POPUP]
    mount: AppExtensionMountEnum
    url: Union[AnyHttpUrl, UrlPathStr]
    permissions: list[Permission] = []

    class Config(ValidationErrorConfig):
        field_errors_map = {
            "permissions": PERMISSION_ERROR_MAPPING,
            "url": URL_PATH_ERROR_MAPPING + URL_ERROR_MAPPING,
        }

    @validator("url")
    def validate_url(cls, v: str, values, **kwargs):
        target = cast(AppExtensionTargetEnum, values.get("target"))
        if (
            not v.startswith("/")
            and target == AppExtensionTargetEnum[AppExtensionTarget.APP_PAGE]
        ):
            msg = "Url cannot start with protocol when target == APP_PAGE"
            raise SaleorValidationError(msg, code=AppErrorCode.INVALID_URL_FORMAT)
        return v


class AuthorStr(ConstrainedStr):
    strip_whitespace = True
    min_length = 1
    max_length = 60


class ManifestBrandLogo(ValidationErrorSchema):
    default: AnyHttpUrl

    class Config(ValidationErrorConfig):
        field_errors_map = {"default": URL_ERROR_MAPPING}


class ManifestBrandData(ValidationErrorSchema):
    logo: ManifestBrandLogo


class Manifest(ValidationErrorSchema):
    id: Annotated[
        str,
        Field(
            max_length=256, description="Id of application used internally by Saleor"
        ),
    ]
    version: Annotated[str, Field(max_length=60, description="App version")]
    name: Annotated[
        str, Field(max_length=60, description="App name displayed in the dashboard")
    ]
    token_target_url: Annotated[
        AnyHttpUrl,
        Field(description="Endpoint used during process of app installation"),
    ]
    about: Annotated[
        Optional[str],
        Field(description="Description of the app displayed in the dashboard"),
    ] = None
    required_saleor_version: Annotated[
        Optional[RequiredSaleorVersionSpec],
        Field(
            description="Version range, in the semver format, which specifies Saleor "
            "version required by the app. The field will be respected starting from "
            "Saleor 3.13"
        ),
    ] = None
    author: Annotated[
        Optional[AuthorStr],
        Field(
            description="App author name displayed in the dashboard "
            "(starting from Saleor 3.13)"
        ),
    ] = None
    app_url: Annotated[
        Optional[AnyHttpUrl], Field(description="App website rendered in the dashboard")
    ] = None
    configuration_url: Annotated[
        Optional[AnyHttpUrl],
        Field(
            description="Address to the app configuration page, which is rendered in "
            "the dashboard (deprecated in Saleor 3.5, use appUrl instead)"
        ),
    ] = None
    data_privacy: Annotated[
        Optional[str],
        Field(
            description="Short description of privacy policy displayed in the "
            "dashboard (deprecated in Saleor 3.5, use dataPrivacyUrl instead)"
        ),
    ] = None
    data_privacy_url: Annotated[
        Optional[AnyHttpUrl], Field(description="URL to the full privacy policy")
    ] = None
    homepage_url: Annotated[
        Optional[AnyHttpUrl], Field(description="External URL to the app homepage")
    ] = None
    support_url: Annotated[
        Optional[AnyHttpUrl],
        Field(
            description="External URL to the page where " "app users can find support"
        ),
    ] = None
    audience: Annotated[Optional[str], Field(max_length=256)] = None
    permissions: Annotated[
        list[Permission],
        Field(description="Array of permissions requested by the app"),
    ] = []
    webhooks: Annotated[
        list[Webhook], Field(description="List of webhooks that will be set")
    ] = []
    extensions: Annotated[
        list[Extension],
        Field(
            description="List of extensions that will be mounted in Saleor's dashboard"
        ),
    ] = []
    brand: Optional[ManifestBrandData] = None

    class Config(ValidationErrorConfig):
        default_error = {"code": AppErrorCode.INVALID}
        root_errors_map = [
            (
                (ValueError, TypeError, UnicodeDecodeError),
                {
                    "code": AppErrorCode.INVALID_MANIFEST_FORMAT,
                    "msg": "Incorrect structure of manifest.",
                },
            )
        ]
        errors_map = {
            MissingError: {"code": AppErrorCode.REQUIRED, "msg": "Field required."},
            UrlError: {"code": AppErrorCode.INVALID_URL_FORMAT},
        }
        field_errors_map = {
            "permissions": PERMISSION_ERROR_MAPPING,
            "token_target_url": URL_ERROR_MAPPING,
            "app_url": URL_ERROR_MAPPING,
            "configuration_url": URL_ERROR_MAPPING,
            "data_privacy_url": URL_ERROR_MAPPING,
            "homepage_url": URL_ERROR_MAPPING,
            "support_url": URL_ERROR_MAPPING,
        }

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
            and v.target != AppExtensionTargetEnum[AppExtensionTarget.APP_PAGE]
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
