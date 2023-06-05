from collections import defaultdict
from enum import Enum
from typing import Any, ClassVar, Optional, Tuple, Type, TypedDict, TypeVar, Union, cast

from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseConfig, BaseModel, ConstrainedDecimal
from pydantic import ValidationError
from pydantic import ValidationError as PydanticValidationError
from pydantic.error_wrappers import ErrorWrapper
from pydantic.utils import ROOT_KEY

T_ERRORS = dict[str, list[DjangoValidationError]]
Loc = Tuple[Union[int, str], ...]
Model = TypeVar("Model", bound="BaseModel")


def to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


class DecimalType(ConstrainedDecimal):
    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        super().__modify_schema__(field_schema)
        field_schema["type"] = ["number", "string"]


class ErrorMapping(TypedDict, total=False):
    code: Enum
    msg: str


FIELD_MAPPING_TYPE = list[
    tuple[Union[Type[Exception], tuple[Type[Exception], ...]], ErrorMapping]
]


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


class ValidationErrorConfig(BaseConfig):
    default_error: Optional[ErrorMapping] = None
    root_errors_map: FIELD_MAPPING_TYPE = []
    errors_map: dict[Type[Exception], ErrorMapping] = {}
    field_errors_map: dict[str, FIELD_MAPPING_TYPE] = {}

    @classmethod
    def get_error_mapping(cls, type_: Type[Exception]) -> Optional[ErrorMapping]:
        for error_type, mapping in cls.errors_map.items():
            if issubclass(type_, error_type):
                return mapping
        return None


class BaseSchema(BaseModel):
    class Config:
        @staticmethod
        def schema_extra(schema: dict[str, Any]) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)


class JsonSchema(BaseSchema):
    class Config:
        alias_generator = to_camel


class ValidationErrorSchema(JsonSchema):
    _fields_mapping: ClassVar[Optional[dict[str, FIELD_MAPPING_TYPE]]] = None

    class Config(ValidationErrorConfig):
        pass

    __config__: ClassVar[Type[ValidationErrorConfig]]

    @classmethod
    def parse_obj(cls: Type[Model], *args, **kwargs) -> Model:
        try:
            return super().parse_obj(*args, **kwargs)
        except PydanticValidationError as error:
            raise translate_validation_error(error)

    @classmethod
    def parse_raw(cls: Type[Model], *args, **kwargs) -> Model:
        try:
            return super().parse_raw(*args, **kwargs)
        except PydanticValidationError as error:
            raise translate_validation_error(error)

    @classmethod
    def get_error_mapping(
        cls: Type["ValidationErrorSchema"],
        field_alias: str,
        error_type: Type[Exception],
    ) -> Optional[ErrorMapping]:
        if cls._fields_mapping is None:
            cls._fields_mapping = {}
            for field_name, field in cls.__fields__.items():
                if mapping := cls.__config__.field_errors_map.get(field_name):
                    cls._fields_mapping[field.alias] = mapping
        if field_alias == ROOT_KEY:
            mappings = cls.__config__.root_errors_map
        else:
            mappings = cls._fields_mapping.get(field_alias, [])
        for type_mappings, error_mapping in mappings:
            if issubclass(error_type, type_mappings):
                return error_mapping
        return None


def get_error_mapping(
    error_type: Type[Exception], config: Type[BaseConfig]
) -> Optional[ErrorMapping]:
    if issubclass(config, ValidationErrorConfig):
        return config.get_error_mapping(error_type)
    return None


def convert_error(error: ErrorWrapper, model, root_config, error_loc):
    code, msg, params = "invalid", str(error.exc), {}
    mapping: Optional[ErrorMapping] = None
    field_name = str(error.loc_tuple()[0])
    if default_error := cast(ErrorMapping, getattr(root_config, "default_error", None)):
        code = default_error["code"].value if "code" in default_error else code
        msg = default_error.get("msg") or msg
    if isinstance(error.exc, SaleorValidationError):
        code = error.exc.mapping["code"].value if "code" in error.exc.mapping else code
        msg = error.exc.mapping.get("msg") or msg
        params = error.exc.params
    if issubclass(model, ValidationErrorSchema):
        mapping = model.get_error_mapping(field_name, error.exc.__class__)
    if not mapping:
        mapping = get_error_mapping(error.exc.__class__, model.__config__)
        mapping = mapping or get_error_mapping(error.exc.__class__, root_config)
    if mapping:
        code = mapping["code"].value if "code" in mapping else code
        msg = mapping.get("msg") or msg
    msg = f"{msg[:1].upper()}{msg[1:]}"
    if msg and msg[-1:] != ".":
        msg += "."
    if field_name == ROOT_KEY:
        return (NON_FIELD_ERRORS,), DjangoValidationError(msg, code=code, params=params)
    return error_loc, DjangoValidationError(msg, code=code, params=params)


def flatten_errors(errors, model, config, loc: Optional[Loc] = None):
    for error in errors:
        if isinstance(error, ErrorWrapper):
            if loc:
                error_loc = loc + error.loc_tuple()
            else:
                error_loc = error.loc_tuple()
            if isinstance(error.exc, ValidationError):
                yield from flatten_errors(
                    error.exc.raw_errors, error.exc.model, config, error_loc
                )
            else:
                yield convert_error(error, model, config, error_loc)
        elif isinstance(error, list):
            yield from flatten_errors(error, model, config, loc)
        else:
            raise RuntimeError(f"Unknown error object: {error}")


def translate_validation_error(error: PydanticValidationError):
    validation_errors: T_ERRORS = defaultdict(list)
    errors, model = error.raw_errors, error.model
    if issubclass(model, BaseModel):
        root_config = model.__config__
    else:
        root_config = model.__pydantic_model__.__config__
    for error_loc, validation_error in flatten_errors(errors, model, root_config):
        field = ".".join([str(loc) for loc in error_loc])
        validation_errors[field].append(validation_error)
    return DjangoValidationError(validation_errors)
