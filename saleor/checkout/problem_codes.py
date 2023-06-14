from enum import Enum


class CheckoutProblemCode(Enum):
    """Definition of all possible checkout problem codes.

    INSUFFICIENT_STOCK - indicates insufficient stock for some variants in checkout
    Placing the order will not be possible until solving this problem.
    """

    INSUFFICIENT_STOCK = "insufficient_stock"


class CheckoutLineProblemCode(Enum):
    """Definition of all possible checkout line problem codes.

    INSUFFICIENT_STOCK - indicates insufficient stock for a given checkout line.
    Placing the order will not be possible until solving this problem.
    """

    INSUFFICIENT_STOCK = "insufficient_stock"
