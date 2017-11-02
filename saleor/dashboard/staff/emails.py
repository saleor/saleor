from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from templated_email import send_templated_mail
from celery import shared_task

from ...settings import DEFAULT_FROM_EMAIL


@shared_task
def send_set_password_email(staff):
    site = Site.objects.get_current()
    ctx = {'protocol': 'http',
           'domain': site.domain,
           'site_name': site.name,
           'uid': urlsafe_base64_encode(force_bytes(staff.pk)),
           'token': default_token_generator.make_token(staff)}
    send_templated_mail(
        template_name='dashboard/staff/set_password',
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[staff.email],
        context=ctx)
