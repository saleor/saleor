from enum import Enum


class GiftCardErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    EXPIRED_GIFT_CARD = "expired_gift_card"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
