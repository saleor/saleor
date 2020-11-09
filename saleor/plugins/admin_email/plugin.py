import logging
from dataclasses import asdict

from django.conf import settings
from django.core.exceptions import ValidationError

from ...core.notify_events import AdminNotifyEvent, NotifyEventType
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..email_common import EmailConfig, validate_email_config
from ..error_codes import PluginErrorCode
from ..models import PluginConfiguration
from .notify_events import (
    send_csv_export_failed,
    send_csv_product_export_success,
    send_set_staff_password_email,
    send_staff_order_confirmation,
)

logger = logging.getLogger(__name__)


event_map = {
    AdminNotifyEvent.STAFF_ORDER_CONFIRMATION: send_staff_order_confirmation,
    AdminNotifyEvent.ACCOUNT_SET_STAFF_PASSWORD: send_set_staff_password_email,
    AdminNotifyEvent.CSV_PRODUCT_EXPORT_SUCCESS: send_csv_product_export_success,
    AdminNotifyEvent.CSV_EXPORT_FAILED: send_csv_export_failed,
}


class AdminEmailPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.notifications.admin_email"
    PLUGIN_NAME = "Admin emails"
    DEFAULT_ACTIVE = True

    DEFAULT_CONFIGURATION = [
        {"name": "host", "value": None},
        {"name": "port", "value": None},
        {"name": "username", "value": None},
        {"name": "password", "value": None},
        {"name": "sender_name", "value": ""},
        {"name": "sender_address", "value": ""},
        {"name": "use_tls", "value": False},
        {"name": "use_ssl", "value": False},
    ]

    CONFIG_STRUCTURE = {
        "host": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The host to use for sending email. Leave it blank if you want to use "
                "system environment - EMAIL_HOST."
            ),
            "label": "SMTP host",
        },
        "port": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Port to use for the SMTP server. Leave it blank if you want to use "
                "system environment - EMAIL_PORT."
            ),
            "label": "SMTP port",
        },
        "username": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Username to use for the SMTP server. Leave it blank if you want to "
                "use system environment - EMAIL_HOST_USER."
            ),
            "label": "SMTP user",
        },
        "password": {
            "type": ConfigurationTypeField.PASSWORD,
            "help_text": (
                "Password to use for the SMTP server. Leave it blank if you want to "
                "use system environment - EMAIL_HOST_PASSWORD."
            ),
            "label": "Password",
        },
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
        "use_tls": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Whether to use a TLS (secure) connection when talking to the SMTP "
                "server. This is used for explicit TLS connections, generally on port "
                "587. Use TLS/Use SSL are mutually exclusive, so only set one of those"
                " settings to True."
            ),
            "label": "Use TLS",
        },
        "use_ssl": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Whether to use an implicit TLS (secure) connection when talking to "
                "the SMTP server. In most email documentation this type of TLS "
                "connection is referred to as SSL. It is generally used on port 465. "
                "Use TLS/Use SSL are mutually exclusive, so only set one of those"
                " settings to True."
            ),
            "label": "Use SSL",
        },
    }

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
            use_tls=configuration["use_tls"],
            use_ssl=configuration["use_ssl"],
        )

    def notify(self, event: NotifyEventType, payload: dict, previous_value):
        if not self.active:
            return previous_value
        if event not in AdminNotifyEvent.CHOICES:
            return previous_value
        if event not in event_map:
            logger.warning(f"Missing handler for event {event}")
            return previous_value
        event_map[event](payload, asdict(self.config))  # type: ignore

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

        if plugin_configuration.active:
            if configuration["use_tls"] and configuration["use_ssl"]:
                error_msg = (
                    "Use TLS and Use SSL are mutually exclusive, so only set one of "
                    "those settings to True."
                )
                raise ValidationError(
                    {
                        "use_ssl": ValidationError(
                            error_msg, code=PluginErrorCode.INVALID.value,
                        ),
                        "use_tls": ValidationError(
                            error_msg, code=PluginErrorCode.INVALID.value,
                        ),
                    }
                )
            config = EmailConfig(**configuration)
            try:
                validate_email_config(config)
            except Exception as e:
                logger.warning("Unable to connect to email backend.", exc_info=e)
                error_msg = (
                    "Unable to connect to email backend. Make sure that you provided "
                    "correct values."
                )
                raise ValidationError(
                    {
                        c: ValidationError(
                            error_msg, code=PluginErrorCode.PLUGIN_MISCONFIGURED.value
                        )
                        for c in configuration.keys()
                    }
                )
