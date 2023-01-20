import logging
import operator
import os
import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from email.headerregistry import Address
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import dateutil.parser
import html2text
import i18naddress
import pybars
from babel.numbers import format_currency
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.core.validators import EmailValidator
from django_prices.utils.locale import get_locale_data

from ..thumbnail.utils import get_thumbnail_size
from .base_plugin import ConfigurationTypeField
from .error_codes import PluginErrorCode

if TYPE_CHECKING:
    from ..plugins.base_plugin import BasePlugin
    from ..plugins.models import PluginConfiguration


logger = logging.getLogger(__name__)


DEFAULT_TEMPLATE_HELP_TEXT = (
    "An HTML template built with Handlebars template language. Leave it "
    "blank if you don't want to send an email for this action. Use the "
    'default Saleor template by providing the "DEFAULT" string as a value.'
)
DEFAULT_SUBJECT_HELP_TEXT = "An email subject built with Handlebars template language."
DEFAULT_EMAIL_VALUE = "DEFAULT"
DEFAULT_EMAIL_TIMEOUT = 5


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
        "help_text": ("The host to use for sending email."),
        "label": "SMTP host",
    },
    "port": {
        "type": ConfigurationTypeField.STRING,
        "help_text": ("Port to use for the SMTP server."),
        "label": "SMTP port",
    },
    "username": {
        "type": ConfigurationTypeField.STRING,
        "help_text": ("Username to use for the SMTP server."),
        "label": "SMTP user",
    },
    "password": {
        "type": ConfigurationTypeField.PASSWORD,
        "help_text": ("Password to use for the SMTP server."),
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
            "587. Use TLS/Use SSL are mutually exclusive, so only set one of these"
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
            "Use TLS/Use SSL are mutually exclusive, so only set one of these"
            " settings to True."
        ),
        "label": "Use SSL",
    },
}


def format_address(this, address, include_phone=True, inline=False, latin=False):
    address["name"] = f"{address.get('first_name', '')} {address.get('last_name', '')}"
    address["country_code"] = address["country"]
    address[
        "street_address"
    ] = f"{address.get('street_address_1','')}\n {address.get('street_address_2','')}"
    address_lines = i18naddress.format_address(address, latin).split("\n")
    phone = address.get("phone")
    if include_phone and phone:
        address_lines.append(str(phone))
    if inline is True:
        return pybars.strlist([", ".join(address_lines)])
    return pybars.strlist(["<br>".join(address_lines)])


def format_datetime(this, date, date_format=None):
    """Convert datetime to a required format."""
    date = dateutil.parser.isoparse(date)
    if date_format is None:
        date_format = "%d-%m-%Y"
    return date.strftime(date_format)


def get_product_image_thumbnail(this, size, image_data):
    """Use provided size to get a correct image."""
    expected_size = get_thumbnail_size(size)
    return image_data["original"][str(expected_size)]


def compare(this, val1, compare_operator, val2):
    """Compare two values based on the provided operator."""
    operators: Dict[str, Callable[[Any, Any], Any]] = {
        "==": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        "<=": operator.le,
        ">=": operator.ge,
        ">": operator.gt,
    }
    if compare_operator not in operators:
        return False
    return operators[compare_operator](val1, val2)


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
    sender_name = config.sender_name or ""
    sender_address = config.sender_address

    from_email = str(Address(sender_name, addr_spec=sender_address))

    email_backend = EmailBackend(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        use_ssl=config.use_ssl,
        use_tls=config.use_tls,
        timeout=DEFAULT_EMAIL_TIMEOUT,
    )
    compiler = pybars.Compiler()
    template = compiler.compile(template_str)
    subject_template = compiler.compile(subject)
    helpers = {
        "format_address": format_address,
        "price": price,
        "format_datetime": format_datetime,
        "get_product_image_thumbnail": get_product_image_thumbnail,
        "compare": compare,
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
        timeout=DEFAULT_EMAIL_TIMEOUT,
    )
    with email_backend:
        # make sure that we have correct config. It will raise error in case when we are
        # not able to log in to email backend.
        pass


def validate_default_email_configuration(
    plugin_configuration: "PluginConfiguration", configuration: dict
):
    """Validate if provided configuration is correct."""

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
        host=configuration["host"],
        port=configuration["port"],
        username=configuration["username"],
        password=configuration["password"],
        sender_name=configuration["sender_name"],
        sender_address=configuration["sender_address"],
        use_tls=configuration["use_tls"],
        use_ssl=configuration["use_ssl"],
    )

    if not config.sender_address:
        raise ValidationError(
            {
                "sender_address": ValidationError(
                    "Missing sender address value.",
                    code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                )
            }
        )

    EmailValidator(
        message={  # type: ignore[arg-type] # the code below is a hack
            "sender_address": ValidationError(
                "Invalid email", code=PluginErrorCode.INVALID.value
            )
        }
    )(config.sender_address)

    try:
        validate_email_config(config)
    except Exception as e:
        logger.warning("Unable to connect to email backend.", exc_info=e)
        error_msg = (
            f"Unable to connect to email backend. Make sure that you provided "
            f"correct values. {e}"
        )

        raise ValidationError(
            {
                c: ValidationError(
                    error_msg, code=PluginErrorCode.PLUGIN_MISCONFIGURED.value
                )
                for c in asdict(config).keys()
            }
        )


def validate_format_of_provided_templates(
    plugin_configuration: "PluginConfiguration",
    email_templates_data: List[Dict],
):
    """Make sure that the templates provided by the user have the correct structure."""
    configuration = plugin_configuration.configuration
    configuration = {item["name"]: item["value"] for item in configuration}

    if not plugin_configuration.active:
        return
    compiler = pybars.Compiler()
    errors: Dict[str, ValidationError] = {}
    for email_data in email_templates_data:
        field: str = email_data["name"]
        template_str = email_data.get("value")
        if not template_str or template_str == DEFAULT_EMAIL_VALUE:
            continue
        try:
            compiler.compile(template_str)
        except pybars.PybarsError:
            errors[field] = ValidationError(
                "The provided template has an inccorect structure.",
                code=PluginErrorCode.INVALID.value,
            )
    if errors:
        raise ValidationError(errors)


def get_email_template(
    plugin: "BasePlugin", template_field_name: str, default: str
) -> str:
    """Get email template from plugin configuration."""
    template_str = default

    if plugin.db_config:
        email_template = plugin.db_config.email_templates.filter(
            name=template_field_name
        ).first()
        if email_template:
            template_str = email_template.value

    return template_str


def get_email_template_or_default(
    plugin: "BasePlugin",
    template_field_name: str,
    default_template_file_name: str,
    default_template_path: str,
):
    email_template_str = DEFAULT_EMAIL_VALUE
    if plugin:
        email_template_str = get_email_template(
            plugin=plugin,
            template_field_name=template_field_name,
            default=DEFAULT_EMAIL_VALUE,
        )
    if email_template_str == DEFAULT_EMAIL_VALUE:
        email_template_str = get_default_email_template(
            default_template_file_name, default_template_path
        )
    return email_template_str


def get_email_subject(
    plugin_configuration: Optional[list],
    subject_field_name: str,
    default: str,
) -> str:
    """Get email subject from plugin configuration."""
    if not plugin_configuration:
        return default
    for config_field in plugin_configuration:
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
