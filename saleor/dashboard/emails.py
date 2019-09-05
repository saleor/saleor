from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from ..account.models import User
from ..celeryconf import app
from ..core.emails import get_email_base_context
from ..core.utils import build_absolute_uri


def send_set_password_staff_email_with_url(redirect_url, staff):
    """Trigger sending a set password email for the given staff."""
    token = default_token_generator.make_token(staff)
    _send_set_user_password_email_with_url.delay(
        staff.email, redirect_url, token, "dashboard/staff/set_password"
    )


def send_set_password_customer_email_with_url(redirect_url, customer):
    """Trigger sending a set password email for the given customer."""
    token = default_token_generator.make_token(customer)
    _send_set_user_password_email_with_url.delay(
        customer.email, redirect_url, token, "dashboard/customer/set_password"
    )


def send_set_password_staff_email(staff):
    """Trigger sending a set password email for the given staff."""
    token = default_token_generator.make_token(staff)
    _send_set_user_password_email.delay(
        staff.email, staff.pk, token, "dashboard/staff/set_password"
    )


def send_set_password_customer_email(customer):
    """Trigger sending a set password email for the given customer."""
    token = default_token_generator.make_token(customer)
    _send_set_user_password_email.delay(
        customer.email, customer.pk, token, "dashboard/customer/set_password"
    )


@app.task
def _send_set_user_password_email_with_url(
    recipient_email, redirect_url, token, template_name
):
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = f"{redirect_url}?%{params}"
    _send_set_password_email(recipient_email, password_set_url, template_name)


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
    ctx = get_email_base_context()
    ctx["password_set_url"] = password_set_url
    send_templated_mail(
        template_name=template_name,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        context=ctx,
    )


@app.task
def send_promote_customer_to_staff_email(staff_pk):
    staff = User.objects.get(pk=staff_pk)
    ctx = get_email_base_context()
    ctx["dashboard_url"] = build_absolute_uri(reverse("dashboard:index"))
    send_templated_mail(
        template_name="dashboard/staff/promote_customer",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[staff.email],
        context=ctx,
    )
