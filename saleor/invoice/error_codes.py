from enum import Enum


class InvoiceErrorCode(Enum):
    REQUIRED = "required"
    NOT_READY = "not_ready"
    URL_NOT_SET = "url_not_set"
    EMAIL_NOT_SET = "email_not_set"
    NUMBER_NOT_SET = "number_not_set"
    NOT_FOUND = "not_found"
    INVALID_STATUS = "invalid_status"
    NO_INVOICE_PLUGIN = "no_invoice_plugin"
