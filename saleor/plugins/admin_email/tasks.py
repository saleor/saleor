from urllib.parse import urlencode

from ...celeryconf import app
from ...core.emails import get_email_context
from ...core.utils.url import prepare_url
from ..email_common import EmailConfig, send_email


@app.task
def send_set_staff_password_email_task(
    recipient_email, redirect_url, token, config: dict
):
    email_config = EmailConfig(**config)
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    _send_set_password_email(recipient_email, password_set_url, email_config)


def _send_set_password_email(recipient_email, password_set_url, config: EmailConfig):
    send_kwargs, ctx = get_email_context()
    ctx["password_set_url"] = password_set_url
    send_email(
        config=config,
        recipient_list=[recipient_email],
        template_name="dashboard/staff/set_password",
        context=ctx,
    )


@app.task
def send_email_with_link_to_download_file_task(
    recipient_email: str, csv_link: str, config: dict
):
    email_config = EmailConfig(**config)
    send_kwargs, ctx = get_email_context()
    ctx["csv_link"] = csv_link
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="csv/export_products_file",
        context=ctx,
    )


@app.task
def send_export_failed_email_task(recipient_email: str, config: dict):
    email_config = EmailConfig(**config)
    send_kwargs, ctx = get_email_context()
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="csv/export_failed",
        context=ctx,
    )


@app.task
def send_staff_order_confirmation_email_task(payload, config: dict):
    email_config = EmailConfig(**config)
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_email(
        config=email_config,
        recipient_list=payload["recipient_list"],
        template_name="order/staff_confirm_order",
        context=ctx,
    )
