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
from . import constants
from .notify_events import (
    send_csv_export_failed,
    send_csv_product_export_success,
    send_set_staff_password_email,
    send_staff_order_confirmation,
    send_staff_reset_password,
)

logger = logging.getLogger(__name__)


@dataclass
class AdminTemplate:
    staff_order_confirmation: Optional[str]
    set_staff_password_email: Optional[str]
    csv_product_export_success: Optional[str]
    csv_export_failed: Optional[str]
    staff_reset_password: Optional[str]


def get_admin_template_map(templates: AdminTemplate):
    return {
        AdminNotifyEvent.STAFF_ORDER_CONFIRMATION: templates.staff_order_confirmation,
        AdminNotifyEvent.ACCOUNT_SET_STAFF_PASSWORD: templates.set_staff_password_email,
        AdminNotifyEvent.CSV_PRODUCT_EXPORT_SUCCESS: (
            templates.csv_product_export_success
        ),
        AdminNotifyEvent.CSV_EXPORT_FAILED: templates.csv_export_failed,
        AdminNotifyEvent.ACCOUNT_STAFF_RESET_PASSWORD: (
            templates.set_staff_password_email
        ),
    }


def get_admin_event_map():
    return {
        AdminNotifyEvent.STAFF_ORDER_CONFIRMATION: send_staff_order_confirmation,
        AdminNotifyEvent.ACCOUNT_SET_STAFF_PASSWORD: send_set_staff_password_email,
        AdminNotifyEvent.ACCOUNT_STAFF_RESET_PASSWORD: send_staff_reset_password,
        AdminNotifyEvent.CSV_PRODUCT_EXPORT_SUCCESS: send_csv_product_export_success,
        AdminNotifyEvent.CSV_EXPORT_FAILED: send_csv_export_failed,
    }


class AdminEmailPlugin(BasePlugin):
    PLUGIN_ID = constants.PLUGIN_ID
    PLUGIN_NAME = "Admin emails"
    PLUGIN_DESCRIPTION = "Plugin responsible for sending the staff emails."
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False

    DEFAULT_CONFIGURATION = [
        {
            "name": constants.STAFF_PASSWORD_RESET_SUBJECT_FIELD,
            "value": constants.STAFF_PASSWORD_RESET_DEFAULT_SUBJECT,
        },
        {
            "name": constants.STAFF_PASSWORD_RESET_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD,
            "value": constants.STAFF_ORDER_CONFIRMATION_DEFAULT_SUBJECT,
        },
        {
            "name": constants.STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.SET_STAFF_PASSWORD_SUBJECT_FIELD,
            "value": constants.SET_STAFF_PASSWORD_DEFAULT_SUBJECT,
        },
        {
            "name": constants.SET_STAFF_PASSWORD_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.CSV_PRODUCT_EXPORT_SUCCESS_SUBJECT_FIELD,
            "value": constants.CSV_PRODUCT_EXPORT_SUCCESS_DEFAULT_SUBJECT,
        },
        {
            "name": constants.CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.CSV_EXPORT_FAILED_SUBJECT_FIELD,
            "value": constants.CSV_EXPORT_FAILED_DEFAULT_SUBJECT,
        },
        {
            "name": constants.CSV_EXPORT_FAILED_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
    ] + DEFAULT_EMAIL_CONFIGURATION  # type: ignore

    CONFIG_STRUCTURE = {
        constants.STAFF_PASSWORD_RESET_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Reset password subject",
        },
        constants.STAFF_PASSWORD_RESET_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Reset password template",
        },
        constants.STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Order confirmation subject",
        },
        constants.STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Order confirmation template",
        },
        constants.SET_STAFF_PASSWORD_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Set password subject",
        },
        constants.SET_STAFF_PASSWORD_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Set password email template",
        },
        constants.CSV_PRODUCT_EXPORT_SUCCESS_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "CSV product export success subject",
        },
        constants.CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "CSV product export success template",
        },
        constants.CSV_EXPORT_FAILED_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "CSV export failed template",
        },
        constants.CSV_EXPORT_FAILED_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "CSV export failed template",
        },
    }
    CONFIG_STRUCTURE.update(DEFAULT_EMAIL_CONFIG_STRUCTURE)
    CONFIG_STRUCTURE["host"][
        "help_text"
    ] += " Leave it blank if you want to use system environment - EMAIL_HOST."
    CONFIG_STRUCTURE["port"][
        "help_text"
    ] += " Leave it blank if you want to use system environment - EMAIL_PORT."
    CONFIG_STRUCTURE["username"][
        "help_text"
    ] += " Leave it blank if you want to use system environment - EMAIL_HOST_USER."
    CONFIG_STRUCTURE["password"][
        "help_text"
    ] += " Leave it blank if you want to use system environment - EMAIL_HOST_PASSWORD."
    CONFIG_STRUCTURE["use_tls"][
        "help_text"
    ] += " Leave it blank if you want to use system environment - EMAIL_USE_TLS."
    CONFIG_STRUCTURE["use_ssl"][
        "help_text"
    ] += " Leave it blank if you want to use system environment - EMAIL_USE_SSL."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = EmailConfig(
            host=configuration["host"] or settings.EMAIL_HOST,
            port=configuration["port"] or settings.EMAIL_PORT,
            username=configuration["username"] or settings.EMAIL_HOST_USER,
            password=configuration["password"] or settings.EMAIL_HOST_PASSWORD,
            sender_name=configuration["sender_name"],
            sender_address=(
                configuration["sender_address"] or settings.DEFAULT_FROM_EMAIL
            ),
            use_tls=configuration["use_tls"] or settings.EMAIL_USE_TLS,
            use_ssl=configuration["use_ssl"] or settings.EMAIL_USE_SSL,
        )

        self.templates = AdminTemplate(
            csv_export_failed=configuration[constants.CSV_EXPORT_FAILED_TEMPLATE_FIELD],
            csv_product_export_success=configuration[
                constants.CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD
            ],
            set_staff_password_email=configuration[
                constants.SET_STAFF_PASSWORD_TEMPLATE_FIELD
            ],
            staff_order_confirmation=configuration[
                constants.STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD
            ],
            staff_reset_password=configuration[
                constants.STAFF_PASSWORD_RESET_TEMPLATE_FIELD
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

        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

        configuration["host"] = configuration["host"] or settings.EMAIL_HOST
        configuration["port"] = configuration["port"] or settings.EMAIL_PORT
        configuration["username"] = (
            configuration["username"] or settings.EMAIL_HOST_USER
        )
        configuration["password"] = (
            configuration["password"] or settings.EMAIL_HOST_PASSWORD
        )
        configuration["sender_address"] = (
            configuration["sender_address"] or settings.DEFAULT_FROM_EMAIL
        )
        configuration["use_tls"] = configuration["use_tls"] or settings.EMAIL_USE_TLS
        configuration["use_ssl"] = configuration["use_ssl"] or settings.EMAIL_USE_SSL

        validate_default_email_configuration(plugin_configuration, configuration)
        validate_format_of_provided_templates(
            plugin_configuration, constants.TEMPLATE_FIELDS
        )
