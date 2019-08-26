from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from templated_email import send_templated_mail

from ..account import events as account_events
from ..celeryconf import app
from ..core.emails import get_email_base_context
from ..core.utils import build_absolute_uri


def send_user_password_reset_email_with_url(redirect_url, user):
    """Trigger sending a password reset email for the given user."""
    token = default_token_generator.make_token(user)
    _send_password_reset_email_with_url.delay(user.email, redirect_url, user.pk, token)


def send_user_password_reset_email(recipient_email, context, user_id):
    """Trigger sending a password reset email for the given user."""
    _send_user_password_reset_email.delay(recipient_email, context, user_id)


@app.task
def _send_user_password_reset_email(recipient_email, context, user_id):
    reset_url = build_absolute_uri(
        reverse(
            "account:reset-password-confirm",
            kwargs={"uidb64": context["uid"], "token": context["token"]},
        )
    )
    _send_password_reset_email(recipient_email, reset_url, user_id)


@app.task
def _send_password_reset_email_with_url(recipient_email, redirect_url, user_id, token):
    params = urlencode({"email": recipient_email, "token": token})
    reset_url = "%(redirect_url)s?%(params)s" % {
        "redirect_url": redirect_url,
        "params": params,
    }
    _send_password_reset_email(recipient_email, reset_url, user_id)


def _send_password_reset_email(recipient_email, reset_url, user_id):
    context = get_email_base_context()
    context["reset_url"] = reset_url
    send_templated_mail(
        template_name="account/password_reset",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        context=context,
    )
    account_events.customer_password_reset_link_sent_event(user_id=user_id)


def send_account_delete_confirmation_email_with_url(redirect_url, user):
    """Trigger sending a account delete email for the given user."""
    token = default_token_generator.make_token(user)
    _send_account_delete_confirmation_email_with_url.delay(
        user.email, redirect_url, token
    )


def send_account_delete_confirmation_email(user):
    """Trigger sending a account delete email for the given user."""
    token = default_token_generator.make_token(user)
    _send_account_delete_confirmation_email.delay(user.email, token)


@app.task
def _send_account_delete_confirmation_email_with_url(
    recipient_email, redirect_url, token
):
    params = urlencode({"token": token})
    delete_url = "%(redirect_url)s?%(params)s" % {
        "redirect_url": redirect_url,
        "params": params,
    }
    _send_account_delete_confirmation_email(recipient_email, delete_url)


@app.task
def _send_account_delete_confirmation_email(recipient_email, token):
    delete_url = build_absolute_uri(
        reverse("account:delete-confirm", kwargs={"token": token})
    )
    _send_delete_confirmation_email(recipient_email, delete_url)


def _send_delete_confirmation_email(recipient_email, delete_url):
    ctx = get_email_base_context()
    ctx["delete_url"] = delete_url
    send_templated_mail(
        template_name="account/account_delete",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        context=ctx,
    )
