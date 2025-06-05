from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"


class NewTabTarget(BaseModel):
    method: Literal["GET", "POST"]

    @field_validator("method")
    @classmethod
    def validate_method(cls, value):
        if value not in [HttpMethod.GET.value, HttpMethod.POST.value]:
            raise ValueError(f"Method must be either {HttpMethod.GET.value} or {HttpMethod.POST.value}")
        return value


class AppExtensionOptions(BaseModel):
    newTabTarget: Optional[NewTabTarget] = None
