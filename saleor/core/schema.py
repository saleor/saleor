import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from functools import partial
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type, Union, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseConfig, BaseModel
from pydantic import ValidationError
from pydantic import ValidationError as PydanticValidationError
from pydantic import validator
from pydantic.error_wrappers import ErrorWrapper, get_exc_type

T_ERRORS = Dict[str, List[DjangoValidationError]]


def to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


@dataclass
class Error:
    code: Optional[Enum] = None
    msg_tmp: Optional[str] = None


class BaseChoice(BaseModel):
    _CHOICES: ClassVar[Dict[str, str]] = {}
    __root__: str

    @validator("__root__")
    def validate(cls, v):
        if v not in cls._CHOICES:
            raise ValueError(f"Allowed values are: {cls._CHOICES.keys()}")
        return cls._CHOICES[v]

    class Config:
        @staticmethod
        def schema_extra(schema: dict[str, Any], model: type["BaseChoice"]) -> None:
            schema.pop("type")
            schema["enum"] = sorted(model._CHOICES.keys())


class BaseSchema(BaseModel):
    class Config(BaseConfig):
        alias_generator = to_camel
        allow_population_by_field_name = True
        json_loads = partial(json.loads, parse_float=Decimal)
        use_enum_values = True


class ValidationErrorConfig(BaseConfig):
    errors_map: Dict[str, Error] = {}
    default_error: Optional[Error] = None
    errors_types_map: Dict[str, Error] = {}


class ValidationErrorMixin(BaseModel):
    __errors_map_cache__: ClassVar[Optional[Dict[str, Error]]] = None

    class Config(ValidationErrorConfig):
        pass

    @classmethod
    def fields_error_map(cls) -> Dict[str, Error]:
        if cls.__errors_map_cache__ is None:
            cls.__errors_map_cache__ = {}
            for field in cls.__fields__.values():
                if field_mapping := cls.__config__.errors_map.get(field.name):
                    cls.__errors_map_cache__[field.alias] = field_mapping
        return cls.__errors_map_cache__

    __config__: ClassVar[Type[Config]]


class Schema(BaseSchema, ValidationErrorMixin):
    class Config(ValidationErrorConfig):
        pass


class SaleorValueError(ValueError):
    def __init__(self, msg: str, code: str, params: Optional[Dict[str, Any]] = None):
        self.msg = msg
        self.code = code
        self.params = params


def error_type_mapping(exc: Type[Exception], config) -> Optional[Error]:
    errors_types_map = getattr(config, "errors_types_map", None)
    if not errors_types_map:
        return None
    error_type = get_exc_type(exc).split(".")
    for i in range(len(error_type), 0, -1):
        if mapping := errors_types_map.get(".".join(error_type[:i])):
            return mapping
    return None


Loc = Tuple[Union[int, str], ...]


def convert_error(error: ErrorWrapper, model, root_config, error_loc):
    if isinstance(error.exc, SaleorValueError):
        yield error_loc[0], DjangoValidationError(
            error.exc.msg, code=error.exc.code, params=error.exc.params
        )
        return
    code: Union[Enum, str] = "invalid"
    msg_template = getattr(error.exc, "msg_template", None)
    params = error.exc.__dict__
    if default_error := getattr(root_config, "default_error", None):
        code = default_error.code or code
        msg_template = default_error.msg_tmp or msg_template
    mapping = error_type_mapping(error.exc.__class__, root_config)
    if issubclass(model, ValidationErrorMixin):
        field_mapping = model.fields_error_map().get(error.loc_tuple()[0])
        mapping = field_mapping or mapping
    if mapping:
        code = mapping.code or code
        msg_template = mapping.msg_tmp or msg_template
    if msg_template:
        msg = msg_template.format(**params)
    else:
        msg = str(error.exc)
    if isinstance(code, Enum):
        code = code.value
    yield error_loc[0], DjangoValidationError(msg, code=cast(str, code), params=params)


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
    for field, validation_error in flatten_errors(errors, model, root_config):
        validation_errors[field].append(validation_error)
    return DjangoValidationError(validation_errors)
