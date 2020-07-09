from enum import Enum


class ExportErrorCode(Enum):
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
