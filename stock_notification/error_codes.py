from enum import Enum


class TransferStockError(str, Enum):
    STOCK_NOT_ENOUGH = "stock_not_enough"
    STOCK_INVALID = "stock_invalid"
