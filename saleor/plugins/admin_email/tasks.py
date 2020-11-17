from urllib.parse import urlencode

from ...celeryconf import app
from ...core.emails import get_email_context
from ...core.utils.url import prepare_url
from ..email_common import (
    EmailConfig,
    get_default_email_template,
    get_email_subject,
    get_email_template,
    send_email,
)
from . import constants


@app.task
def send_set_staff_password_email_task(
    recipient_email, redirect_url, token, config: dict
):
    email_config = EmailConfig(**config)
    email_template_str = get_email_template(
        constants.PLUGIN_ID,
        constants.SET_STAFF_PASSWORD_TEMPLATE_FIELD,
        constants.DEFAULT_EMAIL_VALUE,
    )
    if email_template_str == constants.DEFAULT_EMAIL_VALUE:
        email_template_str = get_default_email_template(
            constants.SET_STAFF_PASSWORD_DEFAULT_TEMPLATE
        )
    subject = get_email_subject(
        constants.PLUGIN_ID,
        constants.SET_STAFF_PASSWORD_TITLE_FIELD,
        constants.SET_STAFF_PASSWORD_DEFAULT_TITLE,
    )
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    send_kwargs, ctx = get_email_context()
    ctx["password_set_url"] = password_set_url
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=ctx,
        subject=subject,
        template_str=email_template_str,
    )


@app.task
def send_email_with_link_to_download_file_task(
    recipient_email: str, csv_link: str, config: dict
):
    email_config = EmailConfig(**config)
    email_template_str = get_email_template(
        constants.PLUGIN_ID,
        constants.CSV_PRODUCT_EXPORT_SUCCESS_TEMPLATE_FIELD,
        constants.DEFAULT_EMAIL_VALUE,
    )
    if email_template_str == constants.DEFAULT_EMAIL_VALUE:
        email_template_str = get_default_email_template(
            constants.CSV_PRODUCT_EXPORT_SUCCESS_DEFAULT_TEMPLATE
        )
    subject = get_email_subject(
        constants.PLUGIN_ID,
        constants.CSV_PRODUCT_EXPORT_SUCCESS_TITLE_FIELD,
        constants.CSV_PRODUCT_EXPORT_SUCCESS_DEFAULT_TITLE,
    )
    send_kwargs, ctx = get_email_context()
    ctx["csv_link"] = csv_link
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        subject=subject,
        template_str=email_template_str,
        context=ctx,
    )


@app.task
def send_export_failed_email_task(recipient_email: str, config: dict):
    email_config = EmailConfig(**config)
    email_template_str = get_email_template(
        constants.PLUGIN_ID,
        constants.CSV_EXPORT_FAILED_TEMPLATE_FIELD,
        constants.DEFAULT_EMAIL_VALUE,
    )
    if email_template_str == constants.DEFAULT_EMAIL_VALUE:
        email_template_str = get_default_email_template(
            constants.CSV_EXPORT_FAILED_TEMPLATE_DEFAULT_TEMPLATE
        )
    subject = get_email_subject(
        constants.PLUGIN_ID,
        constants.CSV_EXPORT_FAILED_TITLE_FIELD,
        constants.CSV_EXPORT_FAILED_DEFAULT_TITLE,
    )
    send_kwargs, ctx = get_email_context()
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        subject=subject,
        template_str=email_template_str,
        context=ctx,
    )


@app.task
def send_staff_order_confirmation_email_task(payload, config: dict):
    email_config = EmailConfig(**config)
    email_template_str = get_email_template(
        constants.PLUGIN_ID,
        constants.STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
        constants.DEFAULT_EMAIL_VALUE,
    )
    if email_template_str == constants.DEFAULT_EMAIL_VALUE:
        email_template_str = get_default_email_template(
            constants.STAFF_ORDER_CONFIRMATION_DEFAULT_TEMPLATE
        )
    subject = get_email_subject(
        constants.PLUGIN_ID,
        constants.STAFF_ORDER_CONFIRMATION_TITLE_FIELD,
        constants.STAFF_ORDER_CONFIRMATION_DEFAULT_TITLE,
    )
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_email(
        config=email_config,
        recipient_list=payload["recipient_list"],
        subject=subject,
        template_str=email_template_str,
        context=payload,
    )
