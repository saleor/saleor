import logging
from dataclasses import dataclass
from email.headerregistry import Address
from typing import Optional

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.mail.backends.smtp import EmailBackend
from templated_email import TemplateBackend

from .base_plugin import ConfigurationTypeField
from .error_codes import PluginErrorCode
from .models import PluginConfiguration

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    host: Optional[str] = None
    port: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    sender_name: Optional[str] = None
    sender_address: Optional[str] = None
    use_tls: bool = False
    use_ssl: bool = False


DEFAULT_EMAIL_CONFIGURATION = [
    {"name": "host", "value": None},
    {"name": "port", "value": None},
    {"name": "username", "value": None},
    {"name": "password", "value": None},
    {"name": "sender_name", "value": ""},
    {"name": "sender_address", "value": ""},
    {"name": "use_tls", "value": False},
    {"name": "use_ssl", "value": False},
]
DEFAULT_EMAIL_CONFIG_STRUCTURE = {
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


def send_email(config: EmailConfig, recipient_list, template_name, context):
    sender_name = config.sender_name
    sender_address = config.sender_address
    if not sender_address or not sender_name:
        # TODO when we deprecate the default mail config from Site, we can drop this if
        # and require the sender's data as a plugin input.
        site = Site.objects.get_current()
        sender_name = sender_name or site.settings.default_mail_sender_name
        sender_address = sender_address or site.settings.default_mail_sender_address
        sender_address = sender_address or settings.DEFAULT_FROM_EMAIL

    from_email = str(Address(sender_name, addr_spec=sender_address))
    email_backend = EmailBackend(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        use_ssl=config.use_ssl,
        use_tls=config.use_tls,
    )
    template_backend = TemplateBackend()
    template_backend.send(
        from_email=from_email,
        connection=email_backend,
        template_name=template_name,
        recipient_list=recipient_list,
        context=context,
    )
    # TODO the template mail will be replaced by the send_mail whith rendered msg by
    # staff user

    # send_mail(
    #     subject,
    #     message,
    #     from_email,
    #     recipient_list,
    #     connection=email_backend
    # )


def validate_email_config(config: EmailConfig):
    email_backend = EmailBackend(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        use_ssl=config.use_ssl,
        use_tls=config.use_tls,
        fail_silently=False,
    )
    try:
        email_backend.open()
    except Exception:
        raise
    finally:
        email_backend.close()


def validate_default_email_configuration(plugin_configuration: "PluginConfiguration"):
    """Validate if provided configuration is correct."""

    configuration = plugin_configuration.configuration
    configuration = {item["name"]: item["value"] for item in configuration}

    if not plugin_configuration.active:
        return

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
