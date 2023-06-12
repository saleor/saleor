import json
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from fnmatch import fnmatchcase
from functools import partial
from typing import Any, ClassVar, Optional, Type, TypedDict, TypeVar, Union

from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseConfig, BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic.utils import ROOT_KEY

Loc = tuple[Union[int, str], ...]
FALLBACK_ERROR_CODE = "invalid"


class ErrorMapping(TypedDict, total=False):
    code: Enum
    msg: str


ERRORS_MAP = dict[str, ErrorMapping]


def to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(map(str.capitalize, components[1:]))


class CustomValueError(ValueError):
    code = "custom"

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[Enum] = None,
        params: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.params = params or {}

    def __str__(self):
        return self.message


class BaseSchema(BaseModel):
    class Config:
        @staticmethod
        def schema_extra(schema: dict[str, Any]) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)


class JsonSchema(BaseSchema):
    class Config:
        alias_generator = to_camel


def _match_error_mapping(error_type: str, mappings: ERRORS_MAP) -> ErrorMapping:
    for pattern, error_mapping in mappings.items():
        if fnmatchcase(error_type, pattern):
            return error_mapping
    return {}


class ValidationErrorConfig(BaseConfig):
    default_error: ErrorMapping = {}
    root_error: ErrorMapping = {}
    errors_map: ERRORS_MAP = {}
    field_errors_map: ERRORS_MAP = {}

    @classmethod
    def get_error_mapping(cls, field_name: str, error_type: str) -> ErrorMapping:
        if mapping := _match_error_mapping(error_type, cls.errors_map):
            return mapping
        return cls.field_errors_map.get(field_name, {})


ValidationErrorSchemaType = TypeVar(
    "ValidationErrorSchemaType", bound="ValidationErrorSchema"
)


class ValidationErrorSchema(JsonSchema):
    _alias_map: ClassVar[Optional[dict[str, str]]] = None
    __config__: ClassVar[Type[ValidationErrorConfig]]

    class Config(ValidationErrorConfig):
        pass

    @classmethod
    def get_field_name(cls, alias: str) -> Optional[str]:
        if cls._alias_map is None:
            cls._alias_map = {}
            for field_name, field in cls.__fields__.items():
                cls._alias_map[field.alias] = field_name
        return cls._alias_map.get(alias)

    @classmethod
    def get_error_mapping(cls, loc: tuple[str, ...], error_type: str) -> ErrorMapping:
        if field_name := cls.get_field_name(loc[0]):
            if mapping := cls.__config__.get_error_mapping(field_name, error_type):
                return mapping
            field = cls.__fields__[field_name]
            if loc[1:] and issubclass(field.type_, ValidationErrorSchema):
                return field.type_.get_error_mapping(loc[1:], error_type)
        return {}

    @classmethod
    def convert_validation_error(
        cls,
        pydantic_error: PydanticValidationError,
        root_error_field: Optional[str] = None,
    ) -> DjangoValidationError:
        validation_errors: dict[str, list[DjangoValidationError]] = defaultdict(list)
        for error in pydantic_error.errors():
            mapping = cls.__config__.default_error.copy()
            field_path = ".".join([str(loc) for loc in error["loc"]])
            loc = tuple([part for part in error["loc"] if isinstance(part, str)])
            mapping.update(cls.get_error_mapping(loc, error["type"]))
            if error["type"] == "value_error.custom":
                if code := error["ctx"].get("error_code"):
                    mapping["code"] = code
                if error["msg"]:
                    mapping["msg"] = error["msg"]
            elif error["loc"] == (ROOT_KEY,):
                mapping.update(cls.__config__.root_error)
                field_path = root_error_field or NON_FIELD_ERRORS
            code = mapping["code"].value if "code" in mapping else FALLBACK_ERROR_CODE
            msg = normalize_error_message(mapping.get("msg") or error["msg"])
            validation_errors[field_path].append(DjangoValidationError(msg, code=code))
        return DjangoValidationError(validation_errors)

    @classmethod
    def parse_obj(
        cls: Type[ValidationErrorSchemaType],
        *args,
        root_error_field: Optional[str] = None,
        **kwargs
    ) -> ValidationErrorSchemaType:
        try:
            return super().parse_obj(*args, **kwargs)
        except PydanticValidationError as error:
            raise cls.convert_validation_error(error, root_error_field)

    @classmethod
    def parse_raw(
        cls: Type[ValidationErrorSchemaType],
        *args,
        root_error_field: Optional[str] = None,
        **kwargs
    ) -> ValidationErrorSchemaType:
        try:
            return super().parse_raw(*args, **kwargs)
        except PydanticValidationError as error:
            raise cls.convert_validation_error(error, root_error_field)


def normalize_error_message(msg: str) -> str:
    msg = f"{msg[:1].upper()}{msg[1:]}"
    if msg and msg[-1:] != ".":
        msg += "."
    return msg


class DecimalType(Decimal):
    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema["type"] = ["number", "string"]


class WebhookResponseBase(BaseSchema):
    class Config:
        allow_mutation = False
        json_loads = partial(json.loads, parse_float=Decimal)
