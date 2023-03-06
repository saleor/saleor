import os

from django.conf import settings

DEFAULT_EMAIL_TEMPLATES_PATH = os.path.join(
    settings.PROJECT_ROOT, "saleor/plugins/admin_email/default_email_templates"
)

STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD = "staff_order_confirmation_template"
SET_STAFF_PASSWORD_TEMPLATE_FIELD = "set_staff_password_template"
CSV_EXPORT_SUCCESS_TEMPLATE_FIELD = "csv_export_success_template"
CSV_EXPORT_FAILED_TEMPLATE_FIELD = "csv_export_failed_template"
STAFF_PASSWORD_RESET_TEMPLATE_FIELD = "staff_password_reset_template"


TEMPLATE_FIELDS = [
    STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
    SET_STAFF_PASSWORD_TEMPLATE_FIELD,
    CSV_EXPORT_SUCCESS_TEMPLATE_FIELD,
    CSV_EXPORT_FAILED_TEMPLATE_FIELD,
    STAFF_PASSWORD_RESET_TEMPLATE_FIELD,
]

SET_STAFF_PASSWORD_DEFAULT_TEMPLATE = "set_password.html"
CSV_EXPORT_SUCCESS_DEFAULT_TEMPLATE = "export_success.html"
CSV_EXPORT_FAILED_TEMPLATE_DEFAULT_TEMPLATE = "export_failed.html"
STAFF_ORDER_CONFIRMATION_DEFAULT_TEMPLATE = "staff_confirm_order.html"
STAFF_PASSWORD_RESET_DEFAULT_TEMPLATE = "password_reset.html"

STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD = "staff_order_confirmation_subject"
SET_STAFF_PASSWORD_SUBJECT_FIELD = "set_staff_password_subject"
CSV_EXPORT_SUCCESS_SUBJECT_FIELD = "csv_export_success_subject"
CSV_EXPORT_FAILED_SUBJECT_FIELD = "csv_export_failed_subject"
STAFF_PASSWORD_RESET_SUBJECT_FIELD = "staff_password_reset_subject"


STAFF_ORDER_CONFIRMATION_DEFAULT_SUBJECT = "Order {{ order.number }} details"
SET_STAFF_PASSWORD_DEFAULT_SUBJECT = "Set Your Dashboard Password"
CSV_EXPORT_SUCCESS_DEFAULT_SUBJECT = "Your exported {{ data_type }} data is ready"
CSV_EXPORT_FAILED_DEFAULT_SUBJECT = "Exporting {{ data_type }} data failed"
STAFF_PASSWORD_RESET_DEFAULT_SUBJECT = "Reset Your Dashboard Password"


PLUGIN_ID = "mirumee.notifications.admin_email"
