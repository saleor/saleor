from celery import shared_task
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from ..core.utils import build_absolute_uri


@shared_task
def send_set_password_email(staff):
    site = Site.objects.get_current()
    ctx = {
        'protocol': 'https' if settings.ENABLE_SSL else 'http',
        'domain': site.domain,
        'site_name': site.name,
        'uid': urlsafe_base64_encode(force_bytes(staff.pk)).decode(),
        'token': default_token_generator.make_token(staff)}
    send_templated_mail(
        template_name='dashboard/staff/set_password',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[staff.email],
        context=ctx)


@shared_task
def send_promote_customer_to_staff_email(staff):
    site = Site.objects.get_current()
    ctx = {
        'protocol': 'https' if settings.ENABLE_SSL else 'http',
        'domain': site.domain,
        'url': build_absolute_uri(reverse('dashboard:index')),
        'site_name': site.name}
    send_templated_mail(
        template_name='dashboard/staff/promote_customer',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[staff.email],
        context=ctx)
