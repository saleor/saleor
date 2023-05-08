from enum import Enum


class PatientErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    ALREADY_EXISTS = "already_exists"
    INACTIVE = "inactive"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    JWT_SIGNATURE_EXPIRED = "signature_has_expired"
    JWT_INVALID_TOKEN = "invalid_token"
    JWT_DECODE_ERROR = "decode_error"
    JWT_MISSING_TOKEN = "missing_token"
    JWT_INVALID_CSRF_TOKEN = "invalid_csrf_token"
