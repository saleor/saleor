from enum import Enum


class DiscountErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
