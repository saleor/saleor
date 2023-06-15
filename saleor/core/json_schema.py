from collections import defaultdict
from enum import Enum
from fnmatch import fnmatchcase
from typing import Any, ClassVar, Optional, Type, TypedDict, TypeVar, Union

from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseConfig, BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic.utils import ROOT_KEY
from pydantic.validators import str_validator

Loc = tuple[Union[int, str], ...]
FALLBACK_ERROR_CODE = "invalid"


class ErrorOverride(TypedDict, total=False):
    code: Enum
    msg: str


ErrorOverrideMap = dict[str, ErrorOverride]


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


class StrFieldMixin:
    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema.update(type="string")

    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        raise NotImplementedError


class BaseSchema(BaseModel):
    class Config:
        @staticmethod
        def schema_extra(schema: dict[str, Any]) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)


class JsonSchema(BaseSchema):
    class Config:
        alias_generator = to_camel


def match_error_override(error_type: str, overrides: ErrorOverrideMap) -> ErrorOverride:
    for pattern, override in overrides.items():
        if fnmatchcase(error_type, pattern):
            return override
    return {}


class ErrorConversionConfig(BaseConfig):
    default_error_override: ErrorOverride = {}
    root_error_override: ErrorOverride = {}
    error_type_overrides: ErrorOverrideMap = {}
    field_error_overrides: ErrorOverrideMap = {}

    @classmethod
    def get_error_override(cls, field_name: str, error_type: str) -> ErrorOverride:
        if override := match_error_override(error_type, cls.error_type_overrides):
            return override
        return cls.field_error_overrides.get(field_name, {})


ErrorConversionModelType = TypeVar(
    "ErrorConversionModelType", bound="ErrorConversionModel"
)


class ErrorConversionModel(JsonSchema):
    _alias_map: ClassVar[Optional[dict[str, str]]] = None
    __config__: ClassVar[Type[ErrorConversionConfig]]

    class Config(ErrorConversionConfig):
        pass

    @classmethod
    def get_field_name(cls, alias: str) -> Optional[str]:
        if cls._alias_map is None:
            cls._alias_map = {}
            for field_name, field in cls.__fields__.items():
                cls._alias_map[field.alias] = field_name
        return cls._alias_map.get(alias)

    @classmethod
    def get_error_override(cls, loc: tuple[str, ...], error_type: str) -> ErrorOverride:
        if field_name := cls.get_field_name(loc[0]):
            if override := cls.__config__.get_error_override(field_name, error_type):
                return override
            field = cls.__fields__[field_name]
            if loc[1:] and issubclass(field.type_, ErrorConversionModel):
                return field.type_.get_error_override(loc[1:], error_type)
        return {}

    @staticmethod
    def normalize_error_message(msg: str) -> str:
        msg = f"{msg[:1].upper()}{msg[1:]}"
        if msg and msg[-1:] != ".":
            msg += "."
        return msg

    @classmethod
    def convert_validation_error(
        cls, pydantic_error: PydanticValidationError, field_name: Optional[str] = None
    ) -> DjangoValidationError:
        validation_errors: dict[str, list[DjangoValidationError]] = defaultdict(list)
        for error in pydantic_error.errors():
            override = cls.__config__.default_error_override.copy()
            field_path = ".".join([str(loc) for loc in error["loc"]])
            loc = tuple([part for part in error["loc"] if isinstance(part, str)])
            override.update(cls.get_error_override(loc, error["type"]))
            if error["type"] == "value_error.custom":
                if code := error["ctx"].get("error_code"):
                    override["code"] = code
                if error["msg"]:
                    override["msg"] = error["msg"]
            elif error["loc"] == (ROOT_KEY,):
                override.update(cls.__config__.root_error_override)
                field_path = field_name or NON_FIELD_ERRORS
            code = override["code"].value if "code" in override else FALLBACK_ERROR_CODE
            msg = cls.normalize_error_message(override.get("msg") or error["msg"])
            validation_errors[field_path].append(DjangoValidationError(msg, code=code))
        return DjangoValidationError(validation_errors)

    @classmethod
    def parse_obj(
        cls: Type[ErrorConversionModelType],
        *args,
        field_name: Optional[str] = None,
        **kwargs
    ) -> ErrorConversionModelType:
        try:
            return super().parse_obj(*args, **kwargs)
        except PydanticValidationError as error:
            raise cls.convert_validation_error(error, field_name)

    @classmethod
    def parse_raw(
        cls: Type[ErrorConversionModelType],
        *args,
        field_name: Optional[str] = None,
        **kwargs
    ) -> ErrorConversionModelType:
        try:
            return super().parse_raw(*args, **kwargs)
        except PydanticValidationError as error:
            raise cls.convert_validation_error(error, field_name)


class WebhookResponseBase(BaseSchema):
    class Config:
        allow_mutation = False
