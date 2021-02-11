from enum import Enum


class ReservationErrorCode(Enum):
    NOT_FOUND = "not_found"
    INVALID_COUNTRY_CODE = "invalid_country_code"
    INSUFFICIENT_STOCK = "insufficient_stock"
    QUANTITY_GREATER_THAN_LIMIT = "quantity_greater_than_limit"
    TOO_MANY_RESERVATIONS = "too_many_reservations"
    UNIQUE = "unique"
    ZERO_QUANTITY = "zero_quantity"
