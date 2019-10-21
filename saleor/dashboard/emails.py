from urllib.parse import urlencode, urlsplit

from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from ..account.models import User
from ..celeryconf import app
from ..core.emails import get_email_context
from ..core.utils import build_absolute_uri


def send_set_password_email_with_url(redirect_url, user, staff=False):
    """Trigger sending a set password email for the given customer/staff."""
    template_type = "staff" if staff else "customer"
    template = f"dashboard/{template_type}/set_password"
    token = default_token_generator.make_token(user)
    _send_set_user_password_email_with_url.delay(
        user.email, redirect_url, token, template
    )


def send_set_password_email(user, staff=False):
    """Trigger sending a set password email for the given customer/staff."""
    template_type = "staff" if staff else "customer"
    template = f"dashboard/{template_type}/set_password"
    token = default_token_generator.make_token(user)
    _send_set_user_password_email.delay(user.email, user.pk, token, template)


@app.task
def _send_set_user_password_email_with_url(
    recipient_email, redirect_url, token, template_name
):
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = urlsplit(redirect_url)
    password_set_url = password_set_url._replace(query=params)
    _send_set_password_email(recipient_email, password_set_url.geturl(), template_name)


@app.task
def _send_set_user_password_email(recipient_email, user_pk, token, template_name):
    uid = urlsafe_base64_encode(force_bytes(user_pk))
    password_set_url = build_absolute_uri(
        reverse(
            "account:reset-password-confirm", kwargs={"token": token, "uidb64": uid}
        )
    )
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


@app.task
def send_promote_customer_to_staff_email(staff_pk):
    staff = User.objects.get(pk=staff_pk)
    send_kwargs, ctx = get_email_context()
    ctx["dashboard_url"] = build_absolute_uri(reverse("dashboard:index"))
    send_templated_mail(
        template_name="dashboard/staff/promote_customer",
        recipient_list=[staff.email],
        context=ctx,
        **send_kwargs,
    )
