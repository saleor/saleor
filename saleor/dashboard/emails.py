from celery import shared_task
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from ..account.models import User
from ..core.emails import get_email_base_context
from ..core.utils import build_absolute_uri


@shared_task
def send_set_password_email(staff_pk):
    staff = User.objects.get(pk=staff_pk)
    uid = urlsafe_base64_encode(force_bytes(staff.pk)).decode()
    token = default_token_generator.make_token(staff)
    password_set_url = build_absolute_uri(
        reverse(
            'account:reset-password-confirm',
            kwargs={'token': token, 'uidb64': uid}))
    ctx = get_email_base_context()
    ctx['password_set_url'] = password_set_url
    send_templated_mail(
        template_name='dashboard/staff/set_password',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[staff.email],
        context=ctx)


@shared_task
def send_promote_customer_to_staff_email(staff_pk):
    staff = User.objects.get(pk=staff_pk)
    ctx = get_email_base_context()
    ctx['dashboard_url'] = build_absolute_uri(reverse('dashboard:index'))
    send_templated_mail(
        template_name='dashboard/staff/promote_customer',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[staff.email],
        context=ctx)
