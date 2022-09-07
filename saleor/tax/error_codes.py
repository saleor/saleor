from enum import Enum


class TaxExemptionManageErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    NOT_EDITABLE_ORDER = "not_editable_order"
