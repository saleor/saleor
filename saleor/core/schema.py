from collections import defaultdict
from enum import Enum
from typing import Any, ClassVar, Optional, Tuple, Type, TypedDict, TypeVar, Union

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
    default_error: ErrorMapping = {}
    root_errors_map: FIELD_MAPPING_TYPE = []
    errors_map: dict[Type[Exception], ErrorMapping] = {}
    field_errors_map: dict[str, FIELD_MAPPING_TYPE] = {}

    @classmethod
    def get_error_mapping(cls, type_: Type[Exception]) -> ErrorMapping:
        for error_type, mapping in cls.errors_map.items():
            if issubclass(type_, error_type):
                return mapping
        return {}


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
    def parse_obj(
        cls: Type[Model], *args, root_error_field: Optional[str] = None, **kwargs
    ) -> Model:
        try:
            return super().parse_obj(*args, **kwargs)
        except PydanticValidationError as error:
            raise translate_validation_error(error, root_error_field)

    @classmethod
    def parse_raw(
        cls: Type[Model], *args, root_error_field: Optional[str] = None, **kwargs
    ) -> Model:
        try:
            return super().parse_raw(*args, **kwargs)
        except PydanticValidationError as error:
            raise translate_validation_error(error, root_error_field)

    @classmethod
    def get_error_mapping(
        cls: Type["ValidationErrorSchema"],
        field_alias: str,
        error_type: Type[Exception],
    ) -> ErrorMapping:
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
        return {}


def get_error_mapping(
    error: ErrorWrapper,
    model: Type[BaseModel],
    root_config: Type[ValidationErrorConfig],
) -> ErrorMapping:
    mapping: ErrorMapping = root_config.default_error.copy()
    mapping.update(root_config.get_error_mapping(error.exc.__class__))
    if issubclass(model, ValidationErrorSchema):
        mapping.update(model.__config__.get_error_mapping(error.exc.__class__))
        field_alias = str(error.loc_tuple()[0])
        field_mapping = model.get_error_mapping(field_alias, error.exc.__class__)
        mapping.update(field_mapping)
    if isinstance(error.exc, SaleorValidationError):
        mapping.update(error.exc.mapping)
    return mapping


def prepare_error_message(msg: str):
    msg = f"{msg[:1].upper()}{msg[1:]}"
    if msg and msg[-1:] != ".":
        msg += "."
    return msg


def convert_error(
    error: ErrorWrapper,
    model: Type[BaseModel],
    root_config: Type[ValidationErrorConfig],
    error_loc: Loc,
) -> tuple[Loc, DjangoValidationError]:
    mapping = get_error_mapping(error, model, root_config)
    code = mapping["code"].value if "code" in mapping else "invalid"
    msg = prepare_error_message(mapping.get("msg") or str(error.exc))
    if error_loc == (ROOT_KEY,):
        return (NON_FIELD_ERRORS,), DjangoValidationError(msg, code=code)
    params = {}
    if isinstance(error.exc, SaleorValidationError):
        params = error.exc.params
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


def translate_validation_error(
    error: PydanticValidationError, root_error_field: Optional[str] = None
):
    validation_errors: T_ERRORS = defaultdict(list)
    errors, model = error.raw_errors, error.model
    if issubclass(model, BaseModel):
        root_config = model.__config__
    else:
        root_config = model.__pydantic_model__.__config__
    for error_loc, validation_error in flatten_errors(errors, model, root_config):
        if root_error_field and error_loc == (NON_FIELD_ERRORS,):
            field = root_error_field
        else:
            field = ".".join([str(loc) for loc in error_loc])
        validation_errors[field].append(validation_error)
    return DjangoValidationError(validation_errors)
