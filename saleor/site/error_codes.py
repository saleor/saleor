from enum import Enum


class SiteErrorCode(Enum):
    FORBIDDEN_CHARACTER = "forbidden_character"
    GRAPHQL_ERROR = "graphql_error"
