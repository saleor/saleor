from urllib.parse import urlencode

from django.contrib.auth.tokens import default_token_generator
from templated_email import send_templated_mail

from ..account import events as account_events
from ..celeryconf import app
from ..core.emails import get_email_context, prepare_url


def send_user_password_reset_email_with_url(redirect_url, user):
    """Trigger sending a password reset email for the given user."""
    token = default_token_generator.make_token(user)
    _send_password_reset_email_with_url.delay(user.email, redirect_url, user.pk, token)


@app.task
def _send_password_reset_email_with_url(recipient_email, redirect_url, user_id, token):
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


def send_account_delete_confirmation_email_with_url(redirect_url, user):
    """Trigger sending a account delete email for the given user."""
    token = default_token_generator.make_token(user)
    _send_account_delete_confirmation_email_with_url.delay(
        user.email, redirect_url, token
    )


@app.task
def _send_account_delete_confirmation_email_with_url(
    recipient_email, redirect_url, token
):
    params = urlencode({"token": token})
    delete_url = "%(redirect_url)s?%(params)s" % {
        "redirect_url": redirect_url,
        "params": params,
    }
    _send_delete_confirmation_email(recipient_email, delete_url)


def _send_delete_confirmation_email(recipient_email, delete_url):
    send_kwargs, ctx = get_email_context()
    ctx["delete_url"] = delete_url
    send_templated_mail(
        template_name="account/account_delete",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


def send_set_password_email_with_url(redirect_url, user, staff=False):
    """Trigger sending a set password email for the given customer/staff."""
    template_type = "staff" if staff else "customer"
    template = f"dashboard/{template_type}/set_password"
    token = default_token_generator.make_token(user)
    _send_set_user_password_email_with_url.delay(
        user.email, redirect_url, token, template
    )


@app.task
def _send_set_user_password_email_with_url(
    recipient_email, redirect_url, token, template_name
):
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    _send_set_password_email(recipient_email, password_set_url, template_name)


def _send_set_password_email(recipient_email, password_set_url, template_name):
    send_kwargs, ctx = get_email_context()
    ctx["password_set_url"] = password_set_url
    send_templated_mail(
        template_name=template_name,
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )
