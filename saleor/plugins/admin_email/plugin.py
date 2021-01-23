import logging
from dataclasses import asdict, dataclass
from typing import Optional

from django.conf import settings

from ...core.notify_events import AdminNotifyEvent, NotifyEventType
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..email_common import (
    DEFAULT_EMAIL_CONFIG_STRUCTURE,
    DEFAULT_EMAIL_CONFIGURATION,
    DEFAULT_EMAIL_VALUE,
    DEFAULT_SUBJECT_HELP_TEXT,
    DEFAULT_TEMPLATE_HELP_TEXT,
    EmailConfig,
    validate_default_email_configuration,
    validate_format_of_provided_templates,
)
from ..models import PluginConfiguration
from .constants import (
    CSV_EXPORT_FAILED_DEFAULT_SUBJECT,
    CSV_EXPORT_FAILED_SUBJECT_FIELD,
    CSV_EXPORT_FAILED_TEMPLATE_FIELD,
    CSV_PRODUCT_EXPORT_SUCCESS_DEFAULT_SUBJECT,
    CSV_PRODUCT_EXPORT_SUCCESS_SUBJECT_FIELD,
    CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD,
    PLUGIN_ID,
    SET_STAFF_PASSWORD_DEFAULT_SUBJECT,
    SET_STAFF_PASSWORD_SUBJECT_FIELD,
    SET_STAFF_PASSWORD_TEMPLATE_FIELD,
    STAFF_ORDER_CONFIRMATION_DEFAULT_SUBJECT,
    STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD,
    STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
    TEMPLATE_FIELDS,
)
from .notify_events import (
    send_csv_export_failed,
    send_csv_product_export_success,
    send_set_staff_password_email,
    send_staff_order_confirmation,
)

logger = logging.getLogger(__name__)


@dataclass
class AdminTemplate:
    staff_order_confirmation: Optional[str]
    set_staff_password_email: Optional[str]
    csv_product_export_success: Optional[str]
    csv_export_failed: Optional[str]


def get_admin_template_map(templates: AdminTemplate):
    return {
        AdminNotifyEvent.STAFF_ORDER_CONFIRMATION: templates.staff_order_confirmation,
        AdminNotifyEvent.ACCOUNT_SET_STAFF_PASSWORD: templates.set_staff_password_email,
        AdminNotifyEvent.CSV_PRODUCT_EXPORT_SUCCESS: (
            templates.csv_product_export_success
        ),
        AdminNotifyEvent.CSV_EXPORT_FAILED: templates.csv_export_failed,
    }


def get_admin_event_map():
    return {
        AdminNotifyEvent.STAFF_ORDER_CONFIRMATION: send_staff_order_confirmation,
        AdminNotifyEvent.ACCOUNT_SET_STAFF_PASSWORD: send_set_staff_password_email,
        AdminNotifyEvent.CSV_PRODUCT_EXPORT_SUCCESS: send_csv_product_export_success,
        AdminNotifyEvent.CSV_EXPORT_FAILED: send_csv_export_failed,
    }


class AdminEmailPlugin(BasePlugin):
    PLUGIN_ID = PLUGIN_ID
    PLUGIN_NAME = "Admin emails"
    DEFAULT_ACTIVE = True

    DEFAULT_CONFIGURATION = [
        {
            "name": STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD,
            "value": STAFF_ORDER_CONFIRMATION_DEFAULT_SUBJECT,
        },
        {"name": STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD, "value": DEFAULT_EMAIL_VALUE},
        {
            "name": SET_STAFF_PASSWORD_SUBJECT_FIELD,
            "value": SET_STAFF_PASSWORD_DEFAULT_SUBJECT,
        },
        {"name": SET_STAFF_PASSWORD_TEMPLATE_FIELD, "value": DEFAULT_EMAIL_VALUE},
        {
            "name": CSV_PRODUCT_EXPORT_SUCCESS_SUBJECT_FIELD,
            "value": CSV_PRODUCT_EXPORT_SUCCESS_DEFAULT_SUBJECT,
        },
        {
            "name": CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": CSV_EXPORT_FAILED_SUBJECT_FIELD,
            "value": CSV_EXPORT_FAILED_DEFAULT_SUBJECT,
        },
        {"name": CSV_EXPORT_FAILED_TEMPLATE_FIELD, "value": DEFAULT_EMAIL_VALUE},
    ] + DEFAULT_EMAIL_CONFIGURATION  # type: ignore

    CONFIG_STRUCTURE = {
        STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Staff order confirmation subject",
        },
        STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Staff order confirmation template",
        },
        SET_STAFF_PASSWORD_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Set staff password subject",
        },
        SET_STAFF_PASSWORD_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Set staff password email template",
        },
        CSV_PRODUCT_EXPORT_SUCCESS_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "CSV product export success subject",
        },
        CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "CSV product export success template",
        },
        CSV_EXPORT_FAILED_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "CSV export failed template",
        },
        CSV_EXPORT_FAILED_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "CSV export failed template",
        },
    }
    CONFIG_STRUCTURE.update(DEFAULT_EMAIL_CONFIG_STRUCTURE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = EmailConfig(
            host=configuration["host"] or settings.EMAIL_HOST,
            port=configuration["port"] or settings.EMAIL_PORT,
            username=configuration["username"] or settings.EMAIL_HOST_USER,
            password=configuration["password"] or settings.EMAIL_HOST_PASSWORD,
            sender_name=configuration["sender_name"],
            sender_address=configuration["sender_address"],
            use_tls=configuration["use_tls"] or settings.EMAIL_USE_TLS,
            use_ssl=configuration["use_ssl"] or settings.EMAIL_USE_SSL,
        )
        self.templates = AdminTemplate(
            csv_export_failed=configuration[CSV_EXPORT_FAILED_TEMPLATE_FIELD],
            csv_product_export_success=configuration[
                CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD
            ],
            set_staff_password_email=configuration[SET_STAFF_PASSWORD_TEMPLATE_FIELD],
            staff_order_confirmation=configuration[
                STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD
            ],
        )

    def notify(self, event: NotifyEventType, payload: dict, previous_value):
        if not self.active:
            return previous_value
        event_map = get_admin_event_map()
        if event not in AdminNotifyEvent.CHOICES:
            return previous_value
        if event not in event_map:
            logger.warning(f"Missing handler for event {event}")
            return previous_value
        template_map = get_admin_template_map(self.templates)
        if not template_map.get(event):
            return previous_value
        event_map[event](payload, asdict(self.config))  # type: ignore

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        validate_default_email_configuration(plugin_configuration)
        validate_format_of_provided_templates(plugin_configuration, TEMPLATE_FIELDS)
