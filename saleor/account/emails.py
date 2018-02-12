from celery import shared_task
from django.conf import settings
from django.urls import reverse
from templated_email import send_templated_mail

from ..core.utils import build_absolute_uri


@shared_task
def send_password_reset_email(context, recipient):
    reset_url = build_absolute_uri(
        reverse(
            'account:reset-password-confirm',
            kwargs={'uidb64': context['uid'], 'token': context['token']}))
    context['reset_url'] = reset_url
    send_templated_mail(
        template_name='source/account/password_reset',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        context=context)
