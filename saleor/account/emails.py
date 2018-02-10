from celery import shared_task
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode
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


@shared_task
def send_activation_mail(user):
    """Sends the e-mail with which a newly registered
    user can verify their e-mail address
    """
    token_generator = default_token_generator
    current_site = Site.objects.get_current()

    context = {
        'protocol': 'https' if settings.ENABLE_SSL else 'http',
        'domain': current_site.domain,
        'uid': force_text(urlsafe_base64_encode(force_bytes(user.pk))),
        'token': token_generator.make_token(user),
        'site_name': current_site.name}

    send_templated_mail(
        'source/account/email_confirmation',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        context=context)
