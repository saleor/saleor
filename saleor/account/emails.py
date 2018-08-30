from celery import shared_task
from django.conf import settings
from django.contrib.sites.models import Site
from django.templatetags.static import static
from django.urls import reverse
from templated_email import send_templated_mail

from ..core.utils import build_absolute_uri


@shared_task
def send_password_reset_email(context, recipient):
    reset_url = build_absolute_uri(
        reverse(
            'account:reset-password-confirm',
            kwargs={
                'uidb64': context['uid'],
                'token': context['token']}))
    logo_url = build_absolute_uri(
        location=None) + static('images/logo-document.svg')
    context['reset_url'] = reset_url
    context['logo_url'] = logo_url
    send_templated_mail(
        template_name='account/password_reset',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        context=context)


@shared_task
def send_account_delete_confirmation_email(token, recipient_email):
    site = Site.objects.get_current()
    logo_url = build_absolute_uri(
        location=None) + static('images/logo-document.svg')
    delete_url = build_absolute_uri(
        reverse('account:delete-confirm', kwargs={'token': token}))
    ctx = {
        'site_name': site.name,
        'domain': site.domain,
        'logo_url': logo_url,
        'url': delete_url}
    send_templated_mail(
        template_name='account/account_delete',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        context=ctx)
