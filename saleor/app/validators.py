import mimetypes
import re
from typing import Annotated, Literal

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from pydantic import BaseModel, Field, field_validator, model_validator

from ..thumbnail import ICON_MIME_TYPES
from .error_codes import AppErrorCode
from .types import AppExtensionHttpMethod


class AppURLValidator(URLValidator):
    validator = URLValidator
    host_re = "(" + validator.hostname_re + validator.domain_re + "|localhost)"
    regex = re.compile(
        r"^(?:[a-z0-9.+-]*)://"  # scheme is validated separately
        r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass authentication
        r"(?:" + validator.ipv4_re + "|" + validator.ipv6_re + "|" + host_re + ")"
        r"(?::\d{2,5})?"  # port
        r"(?:[/?#][^\s]*)?"  # resource path
        r"\Z",
        re.IGNORECASE,
    )


image_url_validator = AppURLValidator(
    message="Incorrect value for field: logo.default.",
    code=AppErrorCode.INVALID_URL_FORMAT.value,
)


def brand_validator(brand):
    if brand is None:
        return
    try:
        logo_url = brand["logo"]["default"]
    except (TypeError, KeyError) as e:
        raise ValidationError(
            "Missing required field: logo.default.", code=AppErrorCode.REQUIRED.value
        ) from e
    image_url_validator(logo_url)
    filetype = mimetypes.guess_type(logo_url)[0]
    if filetype not in ICON_MIME_TYPES:
        raise ValidationError(
            "Invalid file type for field: logo.default.",
            code=AppErrorCode.INVALID_URL_FORMAT.value,
        )


def validate_POST_or_GET_http_method(value):
    """Validate that the HTTP method is either GET or POST."""
    if value not in [
        AppExtensionHttpMethod.GET,
        AppExtensionHttpMethod.POST,
    ]:
        raise ValueError(
            f"Method must be either {AppExtensionHttpMethod.GET} or {AppExtensionHttpMethod.POST}"
        )
    return value


class NewTabTargetOptions(BaseModel):
    method: Literal["GET", "POST"]

    @field_validator("method")
    def validate_method(cls, value):
        return validate_POST_or_GET_http_method(value)


class WidgetTargetOptions(BaseModel):
    method: Literal["GET", "POST"]

    @field_validator("method")
    def validate_method(cls, value):
        return validate_POST_or_GET_http_method(value)


class AppExtensionOptions(BaseModel):
    new_tab_target: Annotated[
        NewTabTargetOptions | None,
        Field(
            validation_alias="newTabTarget",
            description="Settings for extension target NEW_TAB",
        ),
    ] = None
    widget_target: Annotated[
        WidgetTargetOptions | None,
        Field(
            validation_alias="widgetTarget",
            description="Settings for extension target WIDGET",
        ),
    ] = None

    @model_validator(mode="after")
    def validate_either_or(cls, values):
        new_tab = values.new_tab_target
        widget = values.widget_target

        if new_tab and widget:
            raise ValueError("Only one of 'newTabTarget' or 'widgetTarget' can be set.")

        return values
