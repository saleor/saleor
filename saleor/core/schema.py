import json
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from functools import partial
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseConfig, BaseModel
from pydantic import ValidationError
from pydantic import ValidationError as PydanticValidationError
from pydantic import validator
from pydantic.error_wrappers import ErrorWrapper
from pydantic.validators import str_validator

T_ERRORS = Dict[str, List[DjangoValidationError]]


def to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


class ErrorMapping(TypedDict, total=False):
    code: Enum
    msg: str


class SaleorValidationError(ValueError):
    def __init__(
        self,
        msg: Optional[str] = None,
        code: Optional[Enum] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.mapping: ErrorMapping = {}
        if msg:
            self.mapping["msg"] = msg
        if code:
            self.mapping["code"] = code
        self.params = params or {}

    def __str__(self) -> str:
        return self.mapping.get("msg", "")


class StringFieldBase:
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type="string")

    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str):
        return value


class BaseChoice(BaseModel):
    _CHOICES: ClassVar[Dict[str, str]] = {}
    _error_mapping: ClassVar[ErrorMapping] = {}
    __root__: str

    @validator("__root__", pre=True)
    def validate(cls, v):
        if isinstance(v, str) and v in cls._CHOICES:
            return cls._CHOICES[v]
        raise SaleorValidationError(**cls._error_mapping)

    class Config:
        @staticmethod
        def schema_extra(schema: dict[str, Any], model: type["BaseChoice"]) -> None:
            schema.pop("type")
            schema["enum"] = sorted(model._CHOICES.keys())


class ValidationErrorConfig(BaseConfig):
    default_error: Optional[ErrorMapping] = None
    errors_map: Dict[Type[Exception], ErrorMapping] = {}

    @classmethod
    def get_error_mapping(cls, type_: Type[Exception]) -> Optional[ErrorMapping]:
        for error_type, mapping in cls.errors_map.items():
            if issubclass(type_, error_type):
                return mapping
        return None


Model = TypeVar("Model", bound="BaseModel")


class ValidationErrorMixin(BaseModel):
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


class Schema(ValidationErrorMixin):
    class Config(ValidationErrorConfig):
        alias_generator = to_camel
        allow_population_by_field_name = True
        json_loads = partial(json.loads, parse_float=Decimal)
        use_enum_values = True

    __config__: ClassVar[Type[ValidationErrorConfig]]


Loc = Tuple[Union[int, str], ...]


def get_error_mapping(
    error_type: Type[Exception], config: Type[BaseConfig]
) -> Optional[ErrorMapping]:
    if issubclass(config, ValidationErrorConfig):
        return config.get_error_mapping(error_type)
    return None


def convert_error(error: ErrorWrapper, model, root_config, error_loc):
    code: Union[Enum, str] = "invalid"
    error_msg, params = "", {}
    if default_error := cast(ErrorMapping, getattr(root_config, "default_error", None)):
        code = default_error.get("code") or code
        error_msg = default_error.get("msg") or error_msg
    if isinstance(error.exc, SaleorValidationError):
        code = error.exc.mapping.get("code") or code
        error_msg = error.exc.mapping.get("msg") or error_msg
        params = error.exc.params
    mapping = get_error_mapping(error.exc.__class__, model.__config__)
    mapping = mapping or get_error_mapping(error.exc.__class__, root_config)
    if mapping:
        code = mapping.get("code") or code
        error_msg = mapping.get("msg") or error_msg
    if not error_msg:
        error_msg = str(error.exc)
    error_msg = f"{error_msg}." if error_msg[-1:] != "." else error_msg
    error_msg = f"{error_msg[:1].capitalize()}{error_msg[1:]}"
    if isinstance(code, Enum):
        code = code.value
    code = cast(str, code)
    yield error_loc, DjangoValidationError(error_msg, code=code, params=params)


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
                yield from convert_error(error, model, config, error_loc)
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
