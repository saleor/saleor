import mimetypes

from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel
from pydantic_core import PydanticCustomError

from ..thumbnail import ICON_MIME_TYPES
from ..webhook.response_schemas.utils.annotations import DefaultIfNone
from .error_codes import AppErrorCode
from .types import DEFAULT_APP_TARGET
from .validators import AppURLValidator, image_url_validator

EXTENSION_IDENTIFIER_MAX_LENGTH = 256

_CAMEL_CONFIG = ConfigDict(
    extra="ignore",
    populate_by_name=True,
    alias_generator=to_camel,
)


class ManifestBrandLogoSchema(BaseModel):
    model_config = _CAMEL_CONFIG

    default: str

    @field_validator("default")
    @classmethod
    def validate_logo_url(cls, v: str) -> str:
        try:
            image_url_validator(v)
        except DjangoValidationError as e:
            raise PydanticCustomError(
                AppErrorCode.INVALID_URL_FORMAT.value,
                "Incorrect value for field: logo.default.",
                {"error_code": AppErrorCode.INVALID_URL_FORMAT.value},
            ) from e
        filetype = mimetypes.guess_type(v)[0]
        if filetype not in ICON_MIME_TYPES:
            raise PydanticCustomError(
                AppErrorCode.INVALID_URL_FORMAT.value,
                "Invalid file type for field: logo.default.",
                {"error_code": AppErrorCode.INVALID_URL_FORMAT.value},
            )
        return v


class ManifestBrandSchema(BaseModel):
    model_config = _CAMEL_CONFIG

    logo: ManifestBrandLogoSchema


class ManifestExtensionSchema(BaseModel):
    model_config = _CAMEL_CONFIG

    label: str
    url: str
    mount: str
    target: str = DEFAULT_APP_TARGET
    permissions: list[str] = []
    options: dict = {}
    identifier: str | None = None

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str | None) -> str | None:
        """Validate the identifier length.

        Normalization (stripping whitespace, treating blank values as not
        provided) happens later in ``manifest_validations``: the validated
        model returned by ``model_validate`` is discarded, so any value
        returned here would not reach the manifest data. Length is checked
        here because it is a purely structural constraint. The raw value is
        measured (whitespace included) since that is what would be persisted.
        """
        if v is None:
            return None
        if len(v) > EXTENSION_IDENTIFIER_MAX_LENGTH:
            raise PydanticCustomError(
                AppErrorCode.INVALID.value,
                "Identifier is too long. Maximum length is "
                f"{EXTENSION_IDENTIFIER_MAX_LENGTH} characters.",
                {"error_code": AppErrorCode.INVALID.value},
            )
        return v


class ManifestWebhookSchema(BaseModel):
    model_config = _CAMEL_CONFIG

    name: str
    target_url: str
    query: str
    is_active: bool = True
    async_events: list[str] = []
    sync_events: list[str] = []
    custom_headers: dict | None = None

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        url_validator = AppURLValidator(schemes=["http", "https", "awssqs", "gcpubsub"])
        try:
            url_validator(v)
        except (DjangoValidationError, AttributeError) as e:
            raise PydanticCustomError(
                AppErrorCode.INVALID_URL_FORMAT.value,
                "Invalid target url.",
                {"error_code": AppErrorCode.INVALID_URL_FORMAT.value},
            ) from e
        return v


class ManifestSchema(BaseModel):
    model_config = _CAMEL_CONFIG

    id: str
    name: str
    version: str
    about: str | None = None
    permissions: list[str] = []
    app_url: str | None = None
    token_target_url: str | None = None
    data_privacy_url: str | None = None
    homepage_url: str | None = None
    support_url: str | None = None
    audience: str | None = None
    required_saleor_version: str | None = None
    author: str | None = None
    brand: ManifestBrandSchema | None = None
    extensions: DefaultIfNone[list[ManifestExtensionSchema]] = []
    webhooks: DefaultIfNone[list[ManifestWebhookSchema]] = []

    @field_validator("token_target_url")
    @classmethod
    def validate_token_target_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        url_validator = AppURLValidator()
        try:
            url_validator(v)
        except (DjangoValidationError, AttributeError) as e:
            raise PydanticCustomError(
                AppErrorCode.INVALID_URL_FORMAT.value,
                "Invalid target url.",
                {"error_code": AppErrorCode.INVALID_URL_FORMAT.value},
            ) from e
        return v

    @field_validator("author")
    @classmethod
    def validate_author(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if clean := v.strip():
            return clean
        raise PydanticCustomError(
            AppErrorCode.INVALID.value,
            "Incorrect value for field: author",
            {"error_code": AppErrorCode.INVALID.value},
        )
