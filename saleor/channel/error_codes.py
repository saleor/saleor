from enum import Enum


class ChannelErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    CHANNELS_CURRENCY_MUST_BE_THE_SAME = "channels_currency_must_be_the_same"
    CHANNEL_WITH_ORDERS = "channel_with_orders"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
