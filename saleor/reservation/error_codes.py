from enum import Enum


class ReservationErrorCode(Enum):
    QUANTITY_GREATER_THAN_LIMIT = "quantity_greater_than_limit"
    UNIQUE = "unique"
    ZERO_QUANTITY = "zero_quantity"
