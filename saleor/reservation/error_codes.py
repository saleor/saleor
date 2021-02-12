from enum import Enum


class ReservationErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID_COUNTRY_CODE = "invalid_country_code"
    INSUFFICIENT_STOCK = "insufficient_stock"
    NOT_FOUND = "not_found"
    QUANTITY_GREATER_THAN_LIMIT = "quantity_greater_than_limit"
    TOO_MANY_RESERVATIONS = "too_many_reservations"
    UNIQUE = "unique"
    ZERO_QUANTITY = "zero_quantity"
