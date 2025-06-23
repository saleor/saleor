import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any, TypeVar

import pydantic
from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    GetCoreSchemaHandler,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)
from pydantic_core import PydanticOmit, PydanticUseDefault, core_schema

from ....core.utils.metadata_manager import metadata_is_valid
from ....payment import interface

M = TypeVar("M")
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


def skip_invalid_metadata[M](value: M) -> M:
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


def skip_invalid_literal[T](value: T, handler: ValidatorFunctionWrapHandler) -> T:
    try:
        return handler(value)
    except ValidationError as err:
        logger.warning("Skipping invalid literal value: %s", err)
        raise PydanticOmit() from err


OnErrorSkipLiteral = Annotated[T, WrapValidator(skip_invalid_literal)]


class EnumName:
    """Validate and serialize enum by name."""

    def __init__(self, *, ignore_case: bool = False):
        self.ignore_case = ignore_case

    def __get_pydantic_core_schema__(
        self, enum_cls: type[Enum], _handler: GetCoreSchemaHandler
    ):
        name_enum = Enum(  # type: ignore[misc]
            "name_enum", {member.name: member.name for member in enum_cls}
        )

        def enum_or_name(value: Enum | str) -> Enum:
            if isinstance(value, enum_cls):
                return value

            if isinstance(value, str):
                try:
                    if self.ignore_case:
                        return next(
                            member
                            for member in enum_cls
                            if member.name.lower() == value.lower()
                        )
                    return enum_cls[value]
                except (KeyError, StopIteration) as e:
                    raise ValueError(f"Enum name not found: {value}") from e
            raise ValueError(
                f"Expected enum member or name, got {type(value).__name__}: {value}"
            )

        return core_schema.no_info_plain_validator_function(
            enum_or_name,
            json_schema_input_schema=core_schema.enum_schema(
                enum_cls, list(name_enum.__members__.values())
            ),
            ref=enum_cls.__name__,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda e: e.name
            ),
        )


EnumByName = Annotated[T, EnumName()]


class JSONValue:
    """A wrapper to allow Pydantic to generate schema for JsonValue."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Use the original JsonValue schema (full validation)
        json_schema = handler(pydantic.JsonValue)
        return json_schema

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        # Return a standard JSON-compatible schema (no recursion errors)
        Json = Annotated[
            interface.JSONValue,
            Field(title="JsonValue"),
        ]
        return TypeAdapter(Json).json_schema()
