from ...core.notify_events import NotifyEventType
from ..base_plugin import BasePlugin, ConfigurationTypeField
from . import SengridConfiguration


class SengridEmailPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.notifications.sengrid_email"
    PLUGIN_NAME = "Sengrid"
    DEFAULT_ACTIVE = False

    DEFAULT_CONFIGURATION = [
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
        {"name": "api_key", "value": None},
    ]
    CONFIG_STRUCTURE = {
        "account_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for account confirmation.",
            "label": "Template ID for account confirmation",
        },
        "account_set_customer_password_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for account set customer password.",
            "label": "Template ID for account set customer password",
        },
        "account_delete_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for account delete.",
            "label": "Template ID for account delete",
        },
        "account_change_email_confirm_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The dynamic template ID for account change email confirmation."
            ),
            "label": "Template ID for account change email confirm",
        },
        "account_change_email_request_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for account change email request.",
            "label": "Template ID for account change email request",
        },
        "account_password_reset_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for account password reset.",
            "label": "Template ID for account password reset",
        },
        "invoice_ready_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for invoice ready.",
            "label": "Template ID for invoice ready",
        },
        "order_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for order confirmation.",
            "label": "Template ID for order confirmation",
        },
        "order_confirmed_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for order confirmed.",
            "label": "Template ID for order confirmed",
        },
        "order_fulfillment_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for order fulfillment confirmation.",
            "label": "Template ID for order fulfillment confirmation",
        },
        "order_fulfillment_update_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for order fulfillment update",
            "label": "Template ID for order fulfillment update",
        },
        "order_payment_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for order payment confirmation.",
            "label": "Template ID for order payment confirmation",
        },
        "order_canceled_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for order canceled",
            "label": "Template ID for order canceled",
        },
        "order_refund_confirmation_template_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The dynamic template ID for order refund confirmation",
            "label": "Template ID for order refund confirmation",
        },
        "api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "This allows your application to authenticate to our API and send mail."
            ),
            "label": "API key",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = SengridConfiguration(**configuration)

    def notify(self, event: NotifyEventType, payload: dict, previous_value):
        if not self.active:
            return previous_value

    #     event_map = get_admin_event_map()
    #     if event not in AdminNotifyEvent.CHOICES:
    #         return previous_value
    #     if event not in event_map:
    #         logger.warning(f"Missing handler for event {event}")
    #         return previous_value
    #     template_map = get_admin_template_map(self.templates)
    #     if not template_map.get(event):
    #         return previous_value
    #     event_map[event](payload, asdict(self.config))  # type: ignore
