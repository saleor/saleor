import logging
from dataclasses import asdict
from typing import List, Union

from django.conf import settings
from promise.promise import Promise

from ...core.notify_events import AdminNotifyEvent, NotifyEventType
from ...graphql.plugins.dataloaders import EmailTemplatesByPluginConfigurationLoader
from ..base_plugin import BasePlugin, ConfigurationTypeField, PluginConfigurationType
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
from ..models import EmailTemplate, PluginConfiguration
from . import constants
from .notify_events import (
    send_csv_export_failed,
    send_csv_export_success,
    send_set_staff_password_email,
    send_staff_order_confirmation,
    send_staff_reset_password,
)

logger = logging.getLogger(__name__)


def get_admin_event_map():
    return {
        AdminNotifyEvent.STAFF_ORDER_CONFIRMATION: send_staff_order_confirmation,
        AdminNotifyEvent.ACCOUNT_SET_STAFF_PASSWORD: send_set_staff_password_email,
        AdminNotifyEvent.ACCOUNT_STAFF_RESET_PASSWORD: send_staff_reset_password,
        AdminNotifyEvent.CSV_EXPORT_SUCCESS: send_csv_export_success,
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
            "name": constants.CSV_EXPORT_SUCCESS_SUBJECT_FIELD,
            "value": constants.CSV_EXPORT_SUCCESS_DEFAULT_SUBJECT,
        },
        {
            "name": constants.CSV_EXPORT_SUCCESS_TEMPLATE_FIELD,
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
    ] + DEFAULT_EMAIL_CONFIGURATION

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
        constants.CSV_EXPORT_SUCCESS_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "CSV product export success subject",
        },
        constants.CSV_EXPORT_SUCCESS_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "CSV product export success template",
        },
        constants.CSV_EXPORT_FAILED_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "CSV export failed subject",
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

    def resolve_plugin_configuration(
        self, request
    ) -> Union[PluginConfigurationType, Promise[PluginConfigurationType]]:
        # Get email templates from the database and merge them with self.configuration.
        if not self.db_config:
            return self.configuration

        def map_templates_to_configuration(
            email_templates: List["EmailTemplate"],
        ) -> PluginConfigurationType:

            email_template_by_name = {
                email_template.name: email_template
                for email_template in email_templates
            }

            # Merge email templates with `self.configuration` items, preserving the
            # order of keys which is defined in `self.CONFIG_STRUCTURE`.
            configuration = []
            for key in self.CONFIG_STRUCTURE:
                for config_item in self.configuration:
                    if config_item["name"] == key:
                        if key in email_template_by_name:
                            config_item["value"] = email_template_by_name[key].value
                        configuration.append(config_item)

            return configuration

        return (
            EmailTemplatesByPluginConfigurationLoader(request)
            .load(self.db_config.pk)
            .then(map_templates_to_configuration)
        )

    def notify(self, event: Union[NotifyEventType, str], payload: dict, previous_value):
        if not self.active:
            return previous_value

        event_map = get_admin_event_map()
        if event not in AdminNotifyEvent.CHOICES:
            return previous_value

        if event not in event_map:
            logger.warning("Missing handler for event %s", event)
            return previous_value

        event_func = event_map[event]
        config = asdict(self.config)
        event_func(payload, config, self)

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
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

        email_templates_data = kwargs.get("email_templates_data", [])
        validate_format_of_provided_templates(
            plugin_configuration, email_templates_data
        )

    @classmethod
    def save_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", cleaned_data
    ):
        current_config = plugin_configuration.configuration

        configuration_to_update = []
        email_templates_data = []

        for data in cleaned_data.get("configuration", []):
            if data["name"] in constants.TEMPLATE_FIELDS:
                email_templates_data.append(data)
            else:
                configuration_to_update.append(data)

        if configuration_to_update:
            cls._update_config_items(configuration_to_update, current_config)

        if "active" in cleaned_data:
            plugin_configuration.active = cleaned_data["active"]

        cls.validate_plugin_configuration(
            plugin_configuration, email_templates_data=email_templates_data
        )
        cls.pre_save_plugin_configuration(plugin_configuration)

        plugin_configuration.save()

        for et_data in email_templates_data:
            if et_data["value"] != DEFAULT_EMAIL_VALUE:
                EmailTemplate.objects.update_or_create(
                    name=et_data["name"],
                    plugin_configuration=plugin_configuration,
                    defaults={"value": et_data["value"]},
                )

        if plugin_configuration.configuration:
            # Let's add a translated descriptions and labels
            cls._append_config_structure(plugin_configuration.configuration)
        return plugin_configuration
