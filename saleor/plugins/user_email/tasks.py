from urllib.parse import urlencode

from templated_email import send_templated_mail

from ...account import events as account_events
from ...celeryconf import app
from ...core.emails import get_email_context
from ...core.utils.url import prepare_url

REQUEST_EMAIL_CHANGE_TEMPLATE = "account/request_email_change"
EMAIL_CHANGED_NOTIFICATION_TEMPLATE = "account/email_changed_notification"
ACCOUNT_DELETE_TEMPLATE = "account/account_delete"
PASSWORD_RESET_TEMPLATE = "account/password_reset"


@app.task
def send_account_confirmation_email_task(email, token, redirect_url):
    params = urlencode({"email": email, "token": token})
    confirm_url = prepare_url(params, redirect_url)
    send_kwargs, ctx = get_email_context()
    ctx["confirm_url"] = confirm_url
    send_templated_mail(
        template_name="account/confirm",
        recipient_list=[email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_password_reset_email_with_url_task(
    recipient_email, redirect_url, user_id, token
):
    params = urlencode({"email": recipient_email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    _send_password_reset_email(recipient_email, reset_url, user_id)


def _send_password_reset_email(recipient_email, reset_url, user_id):
    send_kwargs, ctx = get_email_context()
    ctx["reset_url"] = reset_url
    send_templated_mail(
        template_name="account/password_reset",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )
    account_events.customer_password_reset_link_sent_event(user_id=user_id)


@app.task
def send_request_email_change_email_task(
    new_email, old_email, redirect_url, user_id, token
):
    params = urlencode({"token": token})
    redirect_url = prepare_url(params, redirect_url)
    send_kwargs, ctx = get_email_context()
    ctx["redirect_url"] = redirect_url
    send_templated_mail(
        template_name=REQUEST_EMAIL_CHANGE_TEMPLATE,
        recipient_list=[new_email],
        context=ctx,
        **send_kwargs,
    )
    account_events.customer_email_change_request_event(
        user_id=user_id, parameters={"old_email": old_email, "new_email": new_email}
    )


@app.task
def send_user_change_email_notification_task(recipient_email):
    send_kwargs, ctx = get_email_context()
    send_templated_mail(
        template_name=EMAIL_CHANGED_NOTIFICATION_TEMPLATE,
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_account_delete_confirmation_email_with_url_task(
    recipient_email, redirect_url, token
):
    params = urlencode({"token": token})
    delete_url = prepare_url(params, redirect_url)
    _send_delete_confirmation_email(recipient_email, delete_url)


def _send_delete_confirmation_email(recipient_email, delete_url):
    send_kwargs, ctx = get_email_context()
    ctx["delete_url"] = delete_url
    send_templated_mail(
        template_name=ACCOUNT_DELETE_TEMPLATE,
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_set_user_password_email_with_url_task(recipient_email, redirect_url, token):
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    _send_set_password_email(recipient_email, password_set_url)


def _send_set_password_email(recipient_email, password_set_url):
    send_kwargs, ctx = get_email_context()
    ctx["password_set_url"] = password_set_url
    send_templated_mail(
        template_name="dashboard/customer/set_password",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )
