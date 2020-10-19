import logging
from dataclasses import dataclass

from ...core.notify_events import NotifyEventType, UserNotifyEvent
from ..base_plugin import BasePlugin
from .emails import *

logger = logging.getLogger(__name__)


@dataclass
class UserEmailConfig:
    account_confirmation_template: str
    account_password_reset_template: str


event_map = {
    UserNotifyEvent.ACCOUNT_CONFIRMATION: handle_account_confirmation,
    UserNotifyEvent.ACCOUNT_SET_CUSTOMER_PASSWORD: handle_account_set_customer_password,
    UserNotifyEvent.ACCOUNT_DELETE: handle_account_delete,
    UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_CONFIRM: handle_account_change_email_confirm,
    UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_REQUEST: handle_account_change_email_request,
    UserNotifyEvent.ACCOUNT_PASSWORD_RESET: handle_account_password_reset_event,
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
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.active = True

    def notify(self, event: NotifyEventType, payload: dict, previous_value):
        if not self.active:
            return previous_value
        if event not in UserNotifyEvent.CHOICES:
            return previous_value
        if event not in event_map:
            logger.warning(f"Missing handler for event {event}")
        event_map[event](payload)
