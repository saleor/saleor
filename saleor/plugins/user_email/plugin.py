import logging
from dataclasses import asdict, dataclass
from typing import Optional

from ...core.notify_events import NotifyEventType, UserNotifyEvent
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
    send_invoice,
    send_order_canceled,
    send_order_confirmation,
    send_order_confirmed,
    send_order_refund,
    send_payment_confirmation,
)

logger = logging.getLogger(__name__)


@dataclass
class UserTemplate:
    account_confirmation: Optional[str]
    account_set_customer_password: Optional[str]
    account_delete: Optional[str]
    account_change_email_confirm: Optional[str]
    account_change_email_request: Optional[str]
    account_password_reset: Optional[str]
    invoice_ready: Optional[str]
    order_confirmation: Optional[str]
    order_confirmed: Optional[str]
    order_fulfillment_confirmation: Optional[str]
    order_fulfillment_update: Optional[str]
    order_payment_confirmation: Optional[str]
    order_canceled: Optional[str]
    order_refund_confirmation: Optional[str]


def get_user_template_map(templates: UserTemplate):
    return {
        UserNotifyEvent.ACCOUNT_CONFIRMATION: templates.account_confirmation,
        UserNotifyEvent.ACCOUNT_SET_CUSTOMER_PASSWORD: (
            templates.account_set_customer_password
        ),
        UserNotifyEvent.ACCOUNT_DELETE: templates.account_delete,
        UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_CONFIRM: (
            templates.account_change_email_confirm
        ),
        UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_REQUEST: (
            templates.account_change_email_request
        ),
        UserNotifyEvent.ACCOUNT_PASSWORD_RESET: templates.account_password_reset,
        UserNotifyEvent.INVOICE_READY: templates.invoice_ready,
        UserNotifyEvent.ORDER_CONFIRMATION: templates.order_confirmation,
        UserNotifyEvent.ORDER_CONFIRMED: templates.order_confirmed,
        UserNotifyEvent.ORDER_FULFILLMENT_CONFIRMATION: (
            templates.order_fulfillment_confirmation
        ),
        UserNotifyEvent.ORDER_FULFILLMENT_UPDATE: templates.order_fulfillment_update,
        UserNotifyEvent.ORDER_PAYMENT_CONFIRMATION: (
            templates.order_payment_confirmation
        ),
        UserNotifyEvent.ORDER_CANCELED: templates.order_canceled,
        UserNotifyEvent.ORDER_REFUND_CONFIRMATION: templates.order_refund_confirmation,
    }


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
        self.templates = UserTemplate(
            account_confirmation=configuration[
                constants.ACCOUNT_CONFIRMATION_TEMPLATE_FIELD
            ],
            account_set_customer_password=configuration[
                constants.ACCOUNT_SET_CUSTOMER_PASSWORD_TEMPLATE_FIELD
            ],
            account_delete=configuration[constants.ACCOUNT_DELETE_TEMPLATE_FIELD],
            account_change_email_confirm=configuration[
                constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_TEMPLATE_FIELD
            ],
            account_change_email_request=configuration[
                constants.ACCOUNT_CHANGE_EMAIL_REQUEST_TEMPLATE_FIELD
            ],
            account_password_reset=configuration[
                constants.ACCOUNT_PASSWORD_RESET_TEMPLATE_FIELD
            ],
            invoice_ready=configuration[constants.INVOICE_READY_TEMPLATE_FIELD],
            order_confirmation=configuration[
                constants.ORDER_CONFIRMATION_TEMPLATE_FIELD
            ],
            order_confirmed=configuration[constants.ORDER_CONFIRMED_TEMPLATE_FIELD],
            order_fulfillment_confirmation=configuration[
                constants.ORDER_FULFILLMENT_CONFIRMATION_TEMPLATE_FIELD
            ],
            order_fulfillment_update=configuration[
                constants.ORDER_FULFILLMENT_UPDATE_TEMPLATE_FIELD
            ],
            order_payment_confirmation=configuration[
                constants.ORDER_PAYMENT_CONFIRMATION_TEMPLATE_FIELD
            ],
            order_canceled=configuration[constants.ORDER_CANCELED_TEMPLATE_FIELD],
            order_refund_confirmation=configuration[
                constants.ORDER_REFUND_CONFIRMATION_TEMPLATE_FIELD
            ],
        )

    def notify(self, event: NotifyEventType, payload: dict, previous_value):
        if not self.active:
            return previous_value
        event_map = get_user_event_map()
        if event not in UserNotifyEvent.CHOICES:
            return previous_value
        if event not in event_map:
            logger.warning(f"Missing handler for event {event}")
            return previous_value
        template_map = get_user_template_map(self.templates)
        if not template_map.get(event):
            return previous_value
        event_map[event](payload, asdict(self.config))  # type: ignore

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

        validate_default_email_configuration(plugin_configuration, configuration)
        validate_format_of_provided_templates(plugin_configuration, TEMPLATE_FIELDS)
