class UserNotifyEvent:
    ACCOUNT_CONFIRMATION = "account_confirmation"
    ACCOUNT_PASSWORD_RESET = "account_password_reset"
    ACCOUNT_CHANGE_EMAIL_REQUEST = "account_change_email_request"
    ACCOUNT_CHANGE_EMAIL_CONFIRM = "account_change_email_confirm"
    ACCOUNT_DELETE = "account_delete"
    ACCOUNT_SET_CUSTOMER_PASSWORD = "account_set_customer_password"

    CHOICES = [
        ACCOUNT_CONFIRMATION,
        ACCOUNT_PASSWORD_RESET,
        ACCOUNT_CHANGE_EMAIL_REQUEST,
        ACCOUNT_CHANGE_EMAIL_CONFIRM,
        ACCOUNT_DELETE,
        ACCOUNT_SET_CUSTOMER_PASSWORD,
    ]


class AdminNotifyEvent:
    ACCOUNT_SET_STAFF_PASSWORD = "account_set_staff_password"
    CSV_PRODUCT_EXPORT_SUCCESS = "csv_export_products_success"
    CSV_EXPORT_FAILED = "csv_export_failed"

    CHOICES = [
        ACCOUNT_SET_STAFF_PASSWORD,
        CSV_PRODUCT_EXPORT_SUCCESS,
        CSV_EXPORT_FAILED,
    ]


class NotifyEventType(UserNotifyEvent, AdminNotifyEvent):
    CHOICES = UserNotifyEvent.CHOICES + AdminNotifyEvent.CHOICES
