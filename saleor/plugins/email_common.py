import logging
import os
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from email.headerregistry import Address
from typing import Optional

import html2text
import i18naddress
import pybars
from babel.numbers import format_currency
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.utils.translation import pgettext
from django_prices.utils.locale import get_locale_data

from .base_plugin import ConfigurationTypeField
from .error_codes import PluginErrorCode
from .models import PluginConfiguration

logger = logging.getLogger(__name__)


DEFAULT_TEMPLATE_MESSAGE = (
    "An HTML template built with handlebars template language. Leave it "
    "blank if you don't want to send an email for this action. Use the "
    "default Saleor template by providing DEFAULT value."
)
DEFAULT_SUBJECT_MESSAGE = "An email subject built with handlebars template language."
DEFAULT_EMAIL_VALUE = "DEFAULT"


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
            " settings to True. Leave it blank if you want to use system environment"
            " - EMAIL_USE_TLS"
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
            " settings to True. Leave it blank if you want to use system environment"
            " - EMAIL_USE_SSL"
        ),
        "label": "Use SSL",
    },
}


def format_address(this, address, include_phone=True, inline=False, latin=False):
    address["name"] = pgettext("Address data", "%(first_name)s %(last_name)s") % address
    address["country_code"] = address["country"]
    address["street_address"] = pgettext(
        "Address data", "%(street_address_1)s\n" "%(street_address_2)s" % address
    )
    address_lines = i18naddress.format_address(address, latin).split("\n")
    phone = address.get("phone")
    if include_phone and phone:
        address_lines.append(str(phone))
    if inline is True:
        return pybars.strlist([", ".join(address_lines)])
    return pybars.strlist(["<br>".join(address_lines)])


def price(this, net_amount, gross_amount, currency, display_gross=False):
    amount = net_amount
    if display_gross:
        amount = gross_amount
    try:
        value = Decimal(amount)
    except (TypeError, InvalidOperation):
        return ""

    locale, locale_code = get_locale_data()
    pattern = locale.currency_formats.get("standard").pattern

    pattern = re.sub("(\xa4+)", '<span class="currency">\\1</span>', pattern)

    formatted_price = format_currency(
        value, currency, format=pattern, locale=locale_code
    )
    return pybars.strlist([formatted_price])


def send_email(
    config: EmailConfig, recipient_list, context, subject="", template_str=""
):
    sender_name = config.sender_name
    sender_address = config.sender_address
    if not sender_address or not sender_name:
        # TODO when we deprecate the default mail config from Site, we can drop this if
        # and require the sender's data as a plugin input or take it from settings file.
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
    compiler = pybars.Compiler()
    template = compiler.compile(template_str)
    subject_template = compiler.compile(subject)
    helpers = {
        "format_address": format_address,
        "price": price,
    }
    message = template(context, helpers=helpers)
    subject_message = subject_template(context, helpers)
    send_mail(
        subject_message,
        html2text.html2text(message),
        from_email,
        recipient_list,
        html_message=message,
        connection=email_backend,
    )


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
                    error_msg,
                    code=PluginErrorCode.INVALID.value,
                ),
                "use_tls": ValidationError(
                    error_msg,
                    code=PluginErrorCode.INVALID.value,
                ),
            }
        )
    config = EmailConfig(
        host=configuration["host"] or settings.EMAIL_HOST,
        port=configuration["port"] or settings.EMAIL_PORT,
        username=configuration["username"] or settings.EMAIL_HOST_USER,
        password=configuration["password"] or settings.EMAIL_HOST_PASSWORD,
        sender_name=configuration["sender_name"],
        sender_address=configuration["sender_address"],
        use_tls=configuration["use_tls"],
        use_ssl=configuration["use_ssl"],
    )
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


def get_email_template(
    plugin_identifier: str, template_field_name: str, default: str
) -> str:
    """Get email template from plugin configuration."""
    plugin_configuration = PluginConfiguration.objects.filter(
        identifier=plugin_identifier
    ).first()
    if not plugin_configuration:
        return default
    configuration = plugin_configuration.configuration
    for config_field in configuration:
        if config_field["name"] == template_field_name:
            return config_field["value"] or default
    return default


def get_email_template_or_default(
    plugin_identifier: str,
    template_field_name: str,
    default_template_file_name: str,
    default_template_path: str,
):
    email_template_str = get_email_template(
        plugin_identifier=plugin_identifier,
        template_field_name=template_field_name,
        default=DEFAULT_EMAIL_VALUE,
    )
    if email_template_str == DEFAULT_EMAIL_VALUE:
        email_template_str = get_default_email_template(
            default_template_file_name, default_template_path
        )
    return email_template_str


def get_email_subject(
    plugin_identifier: str, subject_field_name: str, default: str
) -> str:
    """Get email subject from plugin configuration."""
    plugin_configuration = PluginConfiguration.objects.filter(
        identifier=plugin_identifier
    ).first()
    if not plugin_configuration:
        return default
    configuration = plugin_configuration.configuration
    for config_field in configuration:
        if config_field["name"] == subject_field_name:
            return config_field["value"] or default
    return default


def get_default_email_template(
    template_file_name: str, default_template_path: str
) -> str:
    """Get default template."""
    default_template_path = os.path.join(default_template_path, template_file_name)
    with open(default_template_path) as f:
        template_str = f.read()
        return template_str
