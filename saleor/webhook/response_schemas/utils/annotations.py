import logging
from datetime import UTC, datetime
from typing import Annotated, Any, TypeVar

from pydantic import (
    AfterValidator,
    BeforeValidator,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)
from pydantic_core import PydanticOmit, PydanticUseDefault

from ....core.utils.metadata_manager import metadata_is_valid

M = TypeVar("M")
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


def skip_invalid_metadata(value: M) -> M:
    if not metadata_is_valid(value):
        raise PydanticUseDefault()
    return value


Metadata = Annotated[dict[str, str], BeforeValidator(skip_invalid_metadata)]


def default_if_none(value: Any) -> Any:
    if value is None:
        raise PydanticUseDefault()
    return value


T = TypeVar("T")
DefaultIfNone = Annotated[T, BeforeValidator(default_if_none)]


def skip_invalid(
    value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
) -> Any:
    try:
        return handler(value)
    except ValidationError as err:
        context = info.context or {}
        custom_message = context.get("custom_message", "Skipping invalid value")
        app = context.get("app")
        logger.warning(
            "%s Value: %s Error: %s",
            custom_message,
            value,
            str(err),
            extra={
                "app": app.id if app else None,
            },
        )
        raise PydanticOmit() from err


OnErrorSkip = Annotated[T, WrapValidator(skip_invalid)]


def default_if_invalid(
    value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
) -> Any:
    try:
        return handler(value)
    except ValidationError as err:
        context = info.context or {}
        app = context.get("app")
        logger.warning(
            "Skipping invalid value: %s error: %s",
            value,
            str(err),
            extra={
                "app": app.id if app else None,
                "field_name": info.field_name,
            },
        )
        raise PydanticUseDefault() from err


OnErrorDefault = Annotated[T, WrapValidator(default_if_invalid)]

DatetimeUTC = Annotated[datetime, AfterValidator(lambda v: v.astimezone(UTC))]


def skip_invalid_literal(value: T, handler: ValidatorFunctionWrapHandler) -> T:
    try:
        return handler(value)
    except ValidationError as err:
        logger.warning("Skipping invalid literal value: %s", err)
        raise PydanticOmit() from err


OnErrorSkipLiteral = Annotated[T, WrapValidator(skip_invalid_literal)]
