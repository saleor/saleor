from enum import Enum


class CelebrityErrorCode(Enum):
    CELEBRITY_NOT_FOUND = "celebrity_not_found"
    CELEBRITY_ERROR = "celebrity_error"
    UNKNOWN_ERROR = "unknown_error"
    INVALID_FIRST_NAME = "invalid_first_name"
    INVALID_LAST_NAME = "invalid_last_name"
    INVALID_CELEBRITY = "invalid_celebrity"
    INVALID_PHONE_NUMBER = "invalid_phone_number"
    INVALID_EMAIL = "invalid_email"
    INVALID_FIELD_VALUE = "invalid_field_value"
