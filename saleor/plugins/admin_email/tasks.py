from typing import Optional

from ...celeryconf import app
from ...csv.events import export_failed_info_sent_event, export_file_sent_event
from ..email_common import (
    EmailConfig,
    get_email_subject,
    get_email_template_or_default,
    send_email,
)
from ..models import PluginConfiguration
from . import constants


def get_plugin_configuration() -> Optional[PluginConfiguration]:
    return PluginConfiguration.objects.filter(identifier=constants.PLUGIN_ID).first()


@app.task(compression="zlib")
def send_set_staff_password_email_task(recipient_email, payload, config: dict):
    email_config = EmailConfig(**config)
    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.SET_STAFF_PASSWORD_TEMPLATE_FIELD,
        constants.SET_STAFF_PASSWORD_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    subject = get_email_subject(
        plugin_configuration,
        constants.SET_STAFF_PASSWORD_SUBJECT_FIELD,
        constants.SET_STAFF_PASSWORD_DEFAULT_SUBJECT,
    )
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )


@app.task(compression="zlib")
def send_email_with_link_to_download_file_task(
    recipient_email: str, payload, config: dict
):
    email_config = EmailConfig(**config)
    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD,
        constants.CSV_PRODUCT_EXPORT_SUCCESS_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    subject = get_email_subject(
        plugin_configuration,
        constants.CSV_PRODUCT_EXPORT_SUCCESS_SUBJECT_FIELD,
        constants.CSV_PRODUCT_EXPORT_SUCCESS_DEFAULT_SUBJECT,
    )
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        subject=subject,
        template_str=email_template_str,
        context=payload,
    )
    export_file_sent_event(
        export_file_id=payload["export"]["id"], user_id=payload["export"].get("user_id")
    )


@app.task(compression="zlib")
def send_export_failed_email_task(recipient_email: str, payload: dict, config: dict):
    email_config = EmailConfig(**config)
    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.CSV_EXPORT_FAILED_TEMPLATE_FIELD,
        constants.CSV_EXPORT_FAILED_TEMPLATE_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    subject = get_email_subject(
        plugin_configuration,
        constants.CSV_EXPORT_FAILED_SUBJECT_FIELD,
        constants.CSV_EXPORT_FAILED_DEFAULT_SUBJECT,
    )
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        subject=subject,
        template_str=email_template_str,
        context=payload,
    )
    export_failed_info_sent_event(
        export_file_id=payload["export"]["id"], user_id=payload["export"].get("user_id")
    )


@app.task(compression="zlib")
def send_staff_order_confirmation_email_task(
    recipient_list: str, payload: dict, config: dict
):
    email_config = EmailConfig(**config)
    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
        constants.STAFF_ORDER_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    subject = get_email_subject(
        plugin_configuration,
        constants.STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD,
        constants.STAFF_ORDER_CONFIRMATION_DEFAULT_SUBJECT,
    )
    send_email(
        config=email_config,
        recipient_list=recipient_list,
        subject=subject,
        template_str=email_template_str,
        context=payload,
    )


@app.task(compression="zlib")
def send_staff_password_reset_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)
    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.STAFF_PASSWORD_RESET_TEMPLATE_FIELD,
        constants.STAFF_PASSWORD_RESET_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.STAFF_PASSWORD_RESET_SUBJECT_FIELD,
        constants.STAFF_PASSWORD_RESET_DEFAULT_SUBJECT,
    )
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
