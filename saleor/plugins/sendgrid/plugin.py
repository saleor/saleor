import logging
from dataclasses import asdict
from typing import Union

from django.core.exceptions import ValidationError

from ...core.notify_events import NotifyEventType, UserNotifyEvent
from ...plugins.sendgrid.tasks import send_email_with_dynamic_template_id
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..error_codes import PluginErrorCode
from ..models import PluginConfiguration
from . import SendgridConfiguration
from .tasks import (
    send_account_confirmation_email_task,
    send_account_delete_confirmation_email_task,
    send_fulfillment_confirmation_email_task,
    send_fulfillment_update_email_task,
    send_gift_card_email_task,
    send_invoice_email_task,
    send_order_canceled_email_task,
    send_order_confirmation_email_task,
    send_order_confirmed_email_task,
    send_order_refund_email_task,
    send_password_reset_email_task,
    send_payment_confirmation_email_task,
    send_request_email_change_email_task,
    send_set_user_password_email_task,
    send_user_change_email_notification_task,
)

logger = logging.getLogger(__name__)


EVENT_MAP = {
    UserNotifyEvent.ACCOUNT_CONFIRMATION: (
        send_account_confirmation_email_task,
        "account_confirmation_template_id",
    ),
    UserNotifyEvent.ACCOUNT_SET_CUSTOMER_PASSWORD: (
        send_set_user_password_email_task,
        "account_set_customer_password_template_id",
    ),
    UserNotifyEvent.ACCOUNT_DELETE: (
        send_account_delete_confirmation_email_task,
        "account_delete_template_id",
    ),
    UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_CONFIRM: (
        send_user_change_email_notification_task,
        "account_change_email_confirm_template_id",
    ),
    UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_REQUEST: (
        send_request_email_change_email_task,
        "account_change_email_request_template_id",
    ),
    UserNotifyEvent.ACCOUNT_PASSWORD_RESET: (
        send_password_reset_email_task,
        "account_password_reset_template_id",
    ),
    UserNotifyEvent.INVOICE_READY: (
        send_invoice_email_task,
        "invoice_ready_template_id",
    ),
    UserNotifyEvent.ORDER_CONFIRMATION: (
        send_order_confirmation_email_task,
        "order_confirmation_template_id",
    ),
    UserNotifyEvent.ORDER_CONFIRMED: (
        send_order_confirmed_email_task,
        "order_confirmed_template_id",
    ),
    UserNotifyEvent.ORDER_FULFILLMENT_CONFIRMATION: (
        send_fulfillment_confirmation_email_task,
        "order_fulfillment_confirmation_template_id",
    ),
    UserNotifyEvent.ORDER_FULFILLMENT_UPDATE: (
        send_fulfillment_update_email_task,
        "order_fulfillment_update_template_id",
    ),
    UserNotifyEvent.ORDER_PAYMENT_CONFIRMATION: (
        send_payment_confirmation_email_task,
        "order_payment_confirmation_template_id",
    ),
    UserNotifyEvent.ORDER_CANCELED: (
        send_order_canceled_email_task,
        "order_canceled_template_id",
    ),
    UserNotifyEvent.ORDER_REFUND_CONFIRMATION: (
        send_order_refund_email_task,
        "order_refund_confirmation_template_id",
    ),
    UserNotifyEvent.SEND_GIFT_CARD: (
        send_gift_card_email_task,
        "send_gift_card_template_id",
    ),
}

HELP_TEXT_TEMPLATE = "ID of the dynamic template in Sendgrid"


class SendgridEmailPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.notifications.sendgrid_email"
    PLUGIN_NAME = "Sendgrid"
    DEFAULT_ACTIVE = False
    CONFIGURATION_PER_CHANNEL = True

    DEFAULT_CONFIGURATION = [
        {"name": "sender_name", "value": ""},
        {"name": "sender_address", "value": ""},
        {"name": "account_confirmation_template_id", "value": None},
        {"name": "account_set_customer_password_template_id", "value": None},
        {"name": "account_delete_template_id", "value": None},
        {"name": "account_change_email_confirm_template_id", "value": None},
        {"name": "account_change_email_request_template_id", "value": None},
        {"name": "account_password_reset_template_id", "value": None},
        {"name": "invoice_ready_template_id", "value": None},
        {"name": "order_confirmation_template_id", "value": None},
        {"name": "order_confirmed_template_id", "value": None},
        {"name": "order_fulfillment_confirmation_template_id", "value": None},
        {"name": "order_fulfillment_update_template_id", "value": None},
        {"name": "order_payment_confirmation_template_id", "value": None},
        {"name": "order_canceled_template_id", "value": None},
        {"name": "order_refund_confirmation_template_id", "value": None},
        {"name": "send_gift_card_template_id", "value": None},
        {"name": "api_key", "value": None},
    ]
    CONFIG_STRUCTURE = {
        "sender_name": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Name which will be visible as 'from' name.",
            "label": "Sender name",
        },
        "sender_address": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Sender email which will be visible as 'from' email.",
            "label": "Sender email",
        },
        "account_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Account confirmation email template",
        },
        "account_set_customer_password_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Account set customer password email template",
        },
        "account_delete_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Account delete email template",
        },
        "account_change_email_confirm_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Account change email confirm email template",
        },
        "account_change_email_request_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Account change email request email template",
        },
        "account_password_reset_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Account password reset email template",
        },
        "invoice_ready_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Invoice ready email template",
        },
        "order_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Order confirmation email template",
        },
        "order_confirmed_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for order confirmed.",
            "label": "Order confirmed email template",
        },
        "order_fulfillment_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Order fulfillment confirmation email template",
        },
        "order_fulfillment_update_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Order fulfillment update email template",
        },
        "order_payment_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Order payment confirmation email template",
        },
        "order_canceled_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Order canceled email template",
        },
        "order_refund_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Order refund confirmation email template",
        },
        "send_gift_card_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": HELP_TEXT_TEMPLATE,
            "label": "Send gift card email template",
        },
        "api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Your Sendgrid API key.",
            "label": "API key",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = SendgridConfiguration(**configuration)

    def notify(self, event: Union[NotifyEventType, str], payload: dict, previous_value):
        if not self.active:
            return previous_value

        event_in_notify_event = event in UserNotifyEvent.CHOICES

        if not event_in_notify_event:
            logger.info(f"Send email with event {event} as dynamic template ID.")
            send_email_with_dynamic_template_id.delay(
                payload, event, asdict(self.config)
            )
            return previous_value

        if event not in EVENT_MAP:
            logger.warning(f"Missing handler for event {event}")
            return previous_value

        configuration = {item["name"]: item["value"] for item in self.configuration}

        event_task, event_template = EVENT_MAP.get(event)  # type: ignore
        template_id = configuration.get(event_template)
        if not template_id:
            # the empty fields means that we should not send an email for this event.
            return previous_value

        event_task.delay(payload, asdict(self.config))

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
        """Validate if provided configuration is correct."""
        if not plugin_configuration.active:
            return

        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        api_key = configuration.get("api_key")
        if not api_key:
            error_msg = "Missing SendGrid API Key"
            raise ValidationError(
                {
                    "api_key": ValidationError(
                        error_msg,
                        code=PluginErrorCode.NOT_FOUND.value,
                    ),
                }
            )
