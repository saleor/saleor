import json
import logging
from datetime import UTC, datetime
from typing import Annotated, Any, TypeVar

from pydantic import (
    AfterValidator,
    BeforeValidator,
    Json,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)
from pydantic_core import PydanticOmit, PydanticUseDefault

from ...core.utils.metadata_manager import metadata_is_valid

M = TypeVar("M")
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

DatetimeUTC = Annotated[datetime, AfterValidator(lambda v: v.replace(tzinfo=UTC))]


def skip_invalid_literal(value: T, handler: ValidatorFunctionWrapHandler) -> T:
    try:
        return handler(value)
    except ValidationError as err:
        logger.warning("Skipping invalid literal value: %s", err)
        raise PydanticOmit() from err


OnErrorSkipLiteral = Annotated[T, WrapValidator(skip_invalid_literal)]


def parse_to_raw_string(value: Any) -> str:
    """Ensure the value is serialized into a JSON string.

    Allow proper pydantic validation.
    """
    try:
        return json.dumps(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid value: {value}. Expected JSON format.") from e


JsonData = Annotated[Json, BeforeValidator(parse_to_raw_string)]
