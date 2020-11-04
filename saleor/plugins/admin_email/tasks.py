from urllib.parse import urlencode

from templated_email import send_templated_mail

from ...celeryconf import app
from ...core.emails import get_email_context
from ...core.utils.url import prepare_url


@app.task
def send_set_staff_password_email_task(recipient_email, redirect_url, token):
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    _send_set_password_email(recipient_email, password_set_url)


def _send_set_password_email(recipient_email, password_set_url):
    send_kwargs, ctx = get_email_context()
    ctx["password_set_url"] = password_set_url
    send_templated_mail(
        template_name="dashboard/staff/set_password",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_email_with_link_to_download_file_task(recipient_email: str, csv_link: str):
    send_kwargs, ctx = get_email_context()
    ctx["csv_link"] = csv_link
    send_templated_mail(
        template_name="csv/export_products_file",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_export_failed_email_task(recipient_email: str):
    send_kwargs, ctx = get_email_context()
    send_templated_mail(
        template_name="csv/export_failed",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_staff_order_confirmation_email_task(payload):
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_templated_mail(
        template_name="order/staff_confirm_order",
        recipient_list=payload["recipient_list"],
        context=payload,
        **send_kwargs,
    )
