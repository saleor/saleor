from urllib.parse import urlencode, urlsplit

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.templatetags.static import static
from templated_email import send_templated_mail

from ..celeryconf import app
from ..core.utils import build_absolute_uri


def get_email_context():
    site: Site = Site.objects.get_current()
    logo_url = build_absolute_uri(static("images/logo-light.svg"))
    send_email_kwargs = {"from_email": site.settings.default_from_email}
    email_template_context = {
        "domain": site.domain,
        "logo_url": logo_url,
        "site_name": site.name,
    }
    return send_email_kwargs, email_template_context


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
    password_set_url = urlsplit(redirect_url)
    password_set_url = password_set_url._replace(query=params)
    _send_set_password_email(recipient_email, password_set_url.geturl(), template_name)


def _send_set_password_email(recipient_email, password_set_url, template_name):
    send_kwargs, ctx = get_email_context()
    ctx["password_set_url"] = password_set_url
    send_templated_mail(
        template_name=template_name,
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )
