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
        template_name='account/password_reset',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        context=context)


@shared_task
def send_account_delete_confirmation_email(context=None, recipient=None):
    # TODO - FIXME
    # reset_url = build_absolute_uri(
    #     reverse(
    #         'account:account-delete-confirm',
    #         kwargs={'token': context['token']}))
    # context['delete_url'] = reset_url
    # send_templated_mail(
    #     template_name='account/password_reset',
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     recipient_list=[recipient],
    #     context=context)
    pass
