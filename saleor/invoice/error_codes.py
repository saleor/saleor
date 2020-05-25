from enum import Enum


class InvoiceErrorCode(Enum):
    REQUIRED = "required"
    NOT_READY = "not_ready"
    URL_OR_NUMBER_NOT_SET = "url_or_number_not_set"
    NOT_FOUND = "not_found"
    INVALID_STATUS = "invalid_status"
