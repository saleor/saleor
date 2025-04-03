from typing import Annotated, Any, TypeVar

from pydantic import (
    BeforeValidator,
)
from pydantic_core import PydanticUseDefault

from ...core.utils.metadata_manager import metadata_is_valid


def skip_invalid_metadata(value: Any) -> Any:
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
