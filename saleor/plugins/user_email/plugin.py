import logging
from dataclasses import asdict
from typing import TYPE_CHECKING, List, Union

from promise.promise import Promise

from ...core.notify_events import NotifyEventType, UserNotifyEvent
from ...graphql.plugins.dataloaders import EmailTemplatesByPluginConfigurationLoader
from ...plugins.models import EmailTemplate
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
from . import constants
from .constants import TEMPLATE_FIELDS
from .notify_events import (
    send_account_change_email_confirm,
    send_account_change_email_request,
    send_account_confirmation,
    send_account_delete,
    send_account_password_reset_event,
    send_account_set_customer_password,
    send_fulfillment_confirmation,
    send_fulfillment_update,
    send_gift_card,
    send_invoice,
    send_order_canceled,
    send_order_confirmation,
    send_order_confirmed,
    send_order_refund,
    send_payment_confirmation,
)

if TYPE_CHECKING:
    from ..models import PluginConfiguration


logger = logging.getLogger(__name__)


def get_user_event_map():
    return {
        UserNotifyEvent.ACCOUNT_CONFIRMATION: send_account_confirmation,
        UserNotifyEvent.ACCOUNT_SET_CUSTOMER_PASSWORD: (
            send_account_set_customer_password
        ),
        UserNotifyEvent.ACCOUNT_DELETE: send_account_delete,
        UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_CONFIRM: send_account_change_email_confirm,
        UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_REQUEST: send_account_change_email_request,
        UserNotifyEvent.ACCOUNT_PASSWORD_RESET: send_account_password_reset_event,
        UserNotifyEvent.INVOICE_READY: send_invoice,
        UserNotifyEvent.ORDER_CONFIRMATION: send_order_confirmation,
        UserNotifyEvent.ORDER_CONFIRMED: send_order_confirmed,
        UserNotifyEvent.ORDER_FULFILLMENT_CONFIRMATION: send_fulfillment_confirmation,
        UserNotifyEvent.ORDER_FULFILLMENT_UPDATE: send_fulfillment_update,
        UserNotifyEvent.ORDER_PAYMENT_CONFIRMATION: send_payment_confirmation,
        UserNotifyEvent.ORDER_CANCELED: send_order_canceled,
        UserNotifyEvent.ORDER_REFUND_CONFIRMATION: send_order_refund,
        UserNotifyEvent.SEND_GIFT_CARD: send_gift_card,
    }


class UserEmailPlugin(BasePlugin):
    PLUGIN_ID = constants.PLUGIN_ID
    PLUGIN_NAME = "User emails"
    CONFIGURATION_PER_CHANNEL = True

    DEFAULT_CONFIGURATION = [
        {
            "name": constants.ACCOUNT_CONFIRMATION_SUBJECT_FIELD,
            "value": constants.ACCOUNT_CONFIRMATION_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ACCOUNT_CONFIRMATION_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ACCOUNT_SET_CUSTOMER_PASSWORD_SUBJECT_FIELD,
            "value": constants.ACCOUNT_SET_CUSTOMER_PASSWORD_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ACCOUNT_SET_CUSTOMER_PASSWORD_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ACCOUNT_DELETE_SUBJECT_FIELD,
            "value": constants.ACCOUNT_DELETE_DEFAULT_SUBJECT,
        },
        {"name": constants.ACCOUNT_DELETE_TEMPLATE_FIELD, "value": DEFAULT_EMAIL_VALUE},
        {
            "name": constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_SUBJECT_FIELD,
            "value": constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ACCOUNT_CHANGE_EMAIL_REQUEST_SUBJECT_FIELD,
            "value": constants.ACCOUNT_CHANGE_EMAIL_REQUEST_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ACCOUNT_CHANGE_EMAIL_REQUEST_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ACCOUNT_PASSWORD_RESET_SUBJECT_FIELD,
            "value": constants.ACCOUNT_PASSWORD_RESET_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ACCOUNT_PASSWORD_RESET_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.INVOICE_READY_SUBJECT_FIELD,
            "value": constants.INVOICE_READY_DEFAULT_SUBJECT,
        },
        {"name": constants.INVOICE_READY_TEMPLATE_FIELD, "value": DEFAULT_EMAIL_VALUE},
        {
            "name": constants.ORDER_CONFIRMATION_SUBJECT_FIELD,
            "value": constants.ORDER_CONFIRMATION_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ORDER_CONFIRMATION_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ORDER_CONFIRMED_SUBJECT_FIELD,
            "value": constants.ORDER_CONFIRMED_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ORDER_CONFIRMED_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ORDER_FULFILLMENT_CONFIRMATION_SUBJECT_FIELD,
            "value": constants.ORDER_FULFILLMENT_CONFIRMATION_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ORDER_FULFILLMENT_CONFIRMATION_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ORDER_FULFILLMENT_UPDATE_SUBJECT_FIELD,
            "value": constants.ORDER_FULFILLMENT_UPDATE_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ORDER_FULFILLMENT_UPDATE_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ORDER_PAYMENT_CONFIRMATION_SUBJECT_FIELD,
            "value": constants.ORDER_PAYMENT_CONFIRMATION_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ORDER_PAYMENT_CONFIRMATION_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.ORDER_CANCELED_SUBJECT_FIELD,
            "value": constants.ORDER_CANCELED_DEFAULT_SUBJECT,
        },
        {"name": constants.ORDER_CANCELED_TEMPLATE_FIELD, "value": DEFAULT_EMAIL_VALUE},
        {
            "name": constants.ORDER_REFUND_CONFIRMATION_SUBJECT_FIELD,
            "value": constants.ORDER_REFUND_CONFIRMATION_DEFAULT_SUBJECT,
        },
        {
            "name": constants.ORDER_REFUND_CONFIRMATION_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
        {
            "name": constants.SEND_GIFT_CARD_SUBJECT_FIELD,
            "value": constants.SEND_GIFT_CARD_DEFAULT_SUBJECT,
        },
        {
            "name": constants.SEND_GIFT_CARD_TEMPLATE_FIELD,
            "value": DEFAULT_EMAIL_VALUE,
        },
    ] + DEFAULT_EMAIL_CONFIGURATION  # type: ignore

    CONFIG_STRUCTURE = {
        constants.ACCOUNT_CONFIRMATION_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Account confirmation - subject",
        },
        constants.ACCOUNT_CONFIRMATION_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Account confirmation - template",
        },
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Set customer password - subject",
        },
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Set customer password - template",
        },
        constants.ACCOUNT_DELETE_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Account delete - subject",
        },
        constants.ACCOUNT_DELETE_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Account delete - template",
        },
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Account change email confirm - subject",
        },
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Account change email confirm - template",
        },
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Account change email request - subject",
        },
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Account change email request - template",
        },
        constants.ACCOUNT_PASSWORD_RESET_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Account password reset - subject",
        },
        constants.ACCOUNT_PASSWORD_RESET_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Account password reset - template",
        },
        constants.INVOICE_READY_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Invoice ready - subject",
        },
        constants.INVOICE_READY_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Invoice ready - template",
        },
        constants.ORDER_CONFIRMATION_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Order confirmation - subject",
        },
        constants.ORDER_CONFIRMATION_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Order confirmation - template",
        },
        constants.ORDER_CONFIRMED_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Order confirmed - subject",
        },
        constants.ORDER_CONFIRMED_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Order confirmed - template",
        },
        constants.ORDER_FULFILLMENT_CONFIRMATION_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Order fulfillment confirmation - subject",
        },
        constants.ORDER_FULFILLMENT_CONFIRMATION_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Order fulfillment confirmation - template",
        },
        constants.ORDER_FULFILLMENT_UPDATE_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Order fulfillment update - subject",
        },
        constants.ORDER_FULFILLMENT_UPDATE_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Order fulfillment update - template",
        },
        constants.ORDER_PAYMENT_CONFIRMATION_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Payment confirmation - subject",
        },
        constants.ORDER_PAYMENT_CONFIRMATION_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Payment confirmation - template",
        },
        constants.ORDER_CANCELED_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Order canceled - subject",
        },
        constants.ORDER_CANCELED_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Order canceled - template",
        },
        constants.ORDER_REFUND_CONFIRMATION_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.STRING,
            "help_text": DEFAULT_SUBJECT_HELP_TEXT,
            "label": "Order refund - subject",
        },
        constants.ORDER_REFUND_CONFIRMATION_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Order refund - template",
        },
        constants.SEND_GIFT_CARD_SUBJECT_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Send gift card - subject",
        },
        constants.SEND_GIFT_CARD_TEMPLATE_FIELD: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": DEFAULT_TEMPLATE_HELP_TEXT,
            "label": "Send gift card - template",
        },
    }
    CONFIG_STRUCTURE.update(DEFAULT_EMAIL_CONFIG_STRUCTURE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = EmailConfig(
            host=configuration["host"],
            port=configuration["port"],
            username=configuration["username"],
            password=configuration["password"],
            sender_name=configuration["sender_name"],
            sender_address=configuration["sender_address"],
            use_tls=configuration["use_tls"],
            use_ssl=configuration["use_ssl"],
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

        event_map = get_user_event_map()
        if event not in UserNotifyEvent.CHOICES:
            return previous_value

        if event not in event_map:
            logger.warning(f"Missing handler for event {event}")
            return previous_value

        event_func = event_map[event]
        config = asdict(self.config)  # type: ignore
        event_func(payload, config, self)

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

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
            if data["name"] in TEMPLATE_FIELDS:
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
