from enum import Enum


class MediaCreateErrorCode(Enum):
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    FILE_SIZE_LIMIT_EXCEEDED = "file_size_limit_exceeded"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    INVALID_FILE_TYPE = "invalid_file_type"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNSUPPORTED_MEDIA_PROVIDER = "unsupported_media_provider"
    UNSUPPORTED_MIME_TYPE = "unsupported_mime_type"


class MediaUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"


class MediaDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class MediaReorderErrorCode(Enum):
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    NOT_MEDIA_OWNER = "not_media_owner"
