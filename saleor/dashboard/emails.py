from celery import shared_task
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.templatetags.static import static
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from ..core.utils import build_absolute_uri


@shared_task
def send_set_password_email(staff):
    uid = urlsafe_base64_encode(force_bytes(staff.pk)).decode()
    token = default_token_generator.make_token(staff)
    password_set_url = build_absolute_uri(
        reverse(
            'account:reset-password-confirm',
            kwargs={'token': token, 'uidb64': uid}))
    ctx = get_email_base_context()
    ctx.update({'password_set_url': password_set_url})
    send_templated_mail(
        template_name='dashboard/staff/set_password',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[staff.email],
        context=ctx)


@shared_task
def send_promote_customer_to_staff_email(staff):
    ctx = get_email_base_context()
    ctx.update({'url': build_absolute_uri(reverse('dashboard:index'))})
    send_templated_mail(
        template_name='dashboard/staff/promote_customer',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[staff.email],
        context=ctx)


def get_email_base_context():
    site = Site.objects.get_current()
    logo_url = build_absolute_uri(
        location=None) + static('images/logo-document.svg')
    return {
        'domain': site.domain,
        'logo_url': logo_url,
        'site_name': site.name}
