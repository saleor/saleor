from enum import Enum


class PurchaseOrderErrorCode(Enum):
    """Error codes for purchase order operations."""

    INVALID_WAREHOUSE = "invalid_warehouse"
    WAREHOUSE_NOT_OWNED = "warehouse_not_owned"
    WAREHOUSE_IS_OWNED = "warehouse_is_owned"
    INVALID_VARIANT = "invalid_variant"
    INVALID_QUANTITY = "invalid_quantity"
    INVALID_PRICE = "invalid_price"
    INVALID_CURRENCY = "invalid_currency"
    INVALID_COUNTRY = "invalid_country"
    REQUIRED = "required"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    GRAPHQL_ERROR = "graphql_error"


class ReceiptErrorCode(Enum):
    """Error codes for receipt operations."""

    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    XERO_SYNC_FAILED = "xero_sync_failed"
