from enum import Enum


class OAuth2ErrorCode(Enum):
    USER_NOT_FOUND = "user_not_found"
    OAUTH2_ERROR = "oauth2_error"
    INVALID = "invalid"
