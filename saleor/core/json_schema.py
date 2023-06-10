import json
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from functools import partial
from typing import Any, ClassVar, Optional, Sequence, Type, TypedDict, TypeVar, Union

from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseConfig, BaseModel, ConstrainedDecimal
from pydantic import ValidationError as PydanticValidationError
from pydantic.error_wrappers import ErrorWrapper
from pydantic.utils import ROOT_KEY

Loc = tuple[Union[int, str], ...]
Model = TypeVar("Model", bound="BaseModel")
FALLBACK_ERROR_CODE = "invalid"


class ErrorMapping(TypedDict, total=False):
    code: Enum
    msg: str


ERROR_MAPPING_TYPE = dict[
    Union[Type[Exception], tuple[Type[Exception], ...]], ErrorMapping
]


def to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(map(str.capitalize, components[1:]))


class SaleorValidationError(ValueError):
    def __init__(
        self,
        msg: Optional[str] = None,
        code: Optional[Enum] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        self.mapping: ErrorMapping = {}
        if msg:
            self.mapping["msg"] = msg
        if code:
            self.mapping["code"] = code
        self.params = params or {}

    def __str__(self) -> str:
        return self.mapping.get("msg", "")


class BaseSchema(BaseModel):
    class Config:
        @staticmethod
        def schema_extra(schema: dict[str, Any]) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)


class JsonSchema(BaseSchema):
    class Config:
        alias_generator = to_camel


class ValidationErrorConfig(BaseConfig):
    default_error: ErrorMapping = {}
    errors_map: ERROR_MAPPING_TYPE = {}
    field_errors_map: dict[str, ERROR_MAPPING_TYPE] = {}

    @classmethod
    def get_error_mapping(
        cls, error_type: Type[Exception], skip_default=False
    ) -> ErrorMapping:
        mapping: ErrorMapping = {} if skip_default else cls.default_error.copy()
        for type_mappings, error_mapping in cls.errors_map.items():
            if issubclass(error_type, type_mappings):
                mapping.update(error_mapping)
                break
        return mapping


class ValidationErrorSchema(JsonSchema):
    _field_errors_map: ClassVar[Optional[dict[str, ERROR_MAPPING_TYPE]]] = None
    __config__: ClassVar[Type[ValidationErrorConfig]]

    class Config(ValidationErrorConfig):
        pass

    @classmethod
    def get_field_errors_map(cls) -> dict[str, ERROR_MAPPING_TYPE]:
        if cls._field_errors_map is None:
            cls._field_errors_map = {}
            for field_name, field in cls.__fields__.items():
                if mapping := cls.__config__.field_errors_map.get(field_name):
                    cls._field_errors_map[field.alias] = mapping
            if root_mapping := cls.__config__.field_errors_map.get(ROOT_KEY):
                cls._field_errors_map[ROOT_KEY] = root_mapping
        return cls._field_errors_map

    @classmethod
    def get_error_mapping(
        cls, field_alias: str, error_type: Type[Exception]
    ) -> ErrorMapping:
        mapping = cls.__config__.get_error_mapping(error_type, skip_default=True)
        field_mappings = cls.get_field_errors_map().get(field_alias, {})
        for type_mappings, error_mapping in field_mappings.items():
            if issubclass(error_type, type_mappings):
                mapping.update(error_mapping)
                break
        return mapping

    @classmethod
    def parse_obj(
        cls: Type[Model], *args, root_error_field: Optional[str] = None, **kwargs
    ) -> Model:
        try:
            return super().parse_obj(*args, **kwargs)
        except PydanticValidationError as error:
            raise convert_pydantic_validation_error(error, root_error_field)

    @classmethod
    def parse_raw(
        cls: Type[Model], *args, root_error_field: Optional[str] = None, **kwargs
    ) -> Model:
        try:
            return super().parse_raw(*args, **kwargs)
        except PydanticValidationError as error:
            raise convert_pydantic_validation_error(error, root_error_field)


def get_error_mapping(
    error: ErrorWrapper,
    model: Type[BaseModel],
    root_config: Type[BaseConfig],
) -> ErrorMapping:
    mapping: ErrorMapping = {}
    error_type = error.exc.__class__
    if issubclass(root_config, ValidationErrorConfig):
        mapping.update(root_config.get_error_mapping(error_type))
    if issubclass(model, ValidationErrorSchema):
        field_mapping = model.get_error_mapping(str(error.loc_tuple()[0]), error_type)
        mapping.update(field_mapping)
    if isinstance(error.exc, SaleorValidationError):
        mapping.update(error.exc.mapping)
    return mapping


def normalize_error_message(msg: str) -> str:
    msg = f"{msg[:1].upper()}{msg[1:]}"
    if msg and msg[-1:] != ".":
        msg += "."
    return msg


def convert_error(
    error: ErrorWrapper,
    model: Type[BaseModel],
    root_config: Type[BaseConfig],
    error_loc: Loc,
) -> tuple[Loc, DjangoValidationError]:
    mapping = get_error_mapping(error, model, root_config)
    code = mapping["code"].value if "code" in mapping else FALLBACK_ERROR_CODE
    msg = normalize_error_message(mapping.get("msg") or str(error.exc))
    error_loc = error_loc if error_loc != (ROOT_KEY,) else (NON_FIELD_ERRORS,)
    if isinstance(error.exc, SaleorValidationError):
        return error_loc, DjangoValidationError(msg, code=code, params=error.exc.params)
    return error_loc, DjangoValidationError(msg, code=code)


def flatten_errors(
    errors: Sequence[Union[Sequence, ErrorWrapper]],
    model: Type[BaseModel],
    config: Type[BaseConfig],
    loc: Optional[Loc] = None,
):
    for error in errors:
        if isinstance(error, ErrorWrapper):
            exc = error.exc
            error_loc = (loc or ()) + error.loc_tuple()
            if isinstance(exc, PydanticValidationError):
                if not issubclass(exc.model, BaseModel):
                    raise RuntimeError("Pydantic Dataclasses not supported")
                yield from flatten_errors(exc.raw_errors, exc.model, config, error_loc)
            else:
                yield convert_error(error, model, config, error_loc)
        elif isinstance(error, list):
            yield from flatten_errors(error, model, config, loc)
        else:
            raise RuntimeError(f"Unknown error object: {error}")


def convert_pydantic_validation_error(
    error: PydanticValidationError, field_name: Optional[str] = None
) -> DjangoValidationError:
    validation_errors: dict[str, list[DjangoValidationError]] = defaultdict(list)
    errors, model = error.raw_errors, error.model
    if not issubclass(model, BaseModel):
        raise RuntimeError("Pydantic Dataclasses not supported")
    for error_loc, validation_error in flatten_errors(errors, model, model.__config__):
        if error_loc == (NON_FIELD_ERRORS,) and field_name:
            error_loc = (field_name,)
        field = ".".join([str(loc) for loc in error_loc])
        validation_errors[field].append(validation_error)
    return DjangoValidationError(validation_errors)


class DecimalType(ConstrainedDecimal):
    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        super().__modify_schema__(field_schema)
        field_schema["type"] = ["number", "string"]


class WebhookResponseBase(BaseSchema):
    class Config:
        allow_mutation = False
        json_loads = partial(json.loads, parse_float=Decimal)
