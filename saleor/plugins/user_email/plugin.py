import logging
from dataclasses import dataclass

from ...core.notify_events import NotifyEventType, UserNotifyEvent
from ..base_plugin import BasePlugin
from .emails import (
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
    send_order_refund,
    send_payment_confirmation,
)

logger = logging.getLogger(__name__)


@dataclass
class UserEmailConfig:
    account_confirmation_template: str
    account_password_reset_template: str


event_map = {
    UserNotifyEvent.ACCOUNT_CONFIRMATION: send_account_confirmation,
    UserNotifyEvent.ACCOUNT_SET_CUSTOMER_PASSWORD: send_account_set_customer_password,
    UserNotifyEvent.ACCOUNT_DELETE: send_account_delete,
    UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_CONFIRM: send_account_change_email_confirm,
    UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_REQUEST: send_account_change_email_request,
    UserNotifyEvent.ACCOUNT_PASSWORD_RESET: send_account_password_reset_event,
    UserNotifyEvent.INVOICE_READY: send_invoice,
    UserNotifyEvent.ORDER_CONFIRMATION: send_order_confirmation,
    UserNotifyEvent.ORDER_FULFILLMENT_CONFIRMATION: send_fulfillment_confirmation,
    UserNotifyEvent.ORDER_FULFILLMENT_UPDATE: send_fulfillment_update,
    UserNotifyEvent.ORDER_PAYMENT_CONFIRMATION: send_payment_confirmation,
    UserNotifyEvent.ORDER_CANCELED: send_order_canceled,
    UserNotifyEvent.ORDER_REFUND_CONFIRMATION: send_order_refund,
}


class UserEmailPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.notifications.user_email"
    PLUGIN_NAME = "User emails"
    # TODO the configuration will be implemented in separate pull request

    # DEFAULT_CONFIGURATION = [
    #     {"name": "account-confirmation_template", "value": None},
    #     {"name": "account-password-reset-template", "value": None},
    # ]
    #
    # CONFIG_STRUCTURE = {
    #     "account-confirmation_template": {
    #         "type": ConfigurationTypeField.SECRET,
    #         "help_text": "",
    #         "label": "Account confirmation template",
    #     },
    #     "account-password-reset-template": {
    #         "type": ConfigurationTypeField.SECRET,
    #         "help_text": "",
    #         "label": "Account password reset template",
    #     },
    # }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # configuration = {item["name"]: item["value"] for item in self.configuration}
        self.active = True

    def notify(self, event: NotifyEventType, payload: dict, previous_value):
        if not self.active:
            return previous_value

        if event not in UserNotifyEvent.CHOICES:
            return previous_value
        if event not in event_map:
            logger.warning(f"Missing handler for event {event}")
            return previous_value
        event_map[event](payload)  # type: ignore
