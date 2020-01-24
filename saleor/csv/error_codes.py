from enum import Enum


class CsvErrorCode(Enum):
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
