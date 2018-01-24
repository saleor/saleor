from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from django.urls import reverse
from templated_email import send_templated_mail


def send_activation_mail(request, user):
    token_generator = default_token_generator
    current_site = get_current_site(request)

    context = {'domain': current_site.domain,
               'site_name': current_site.name,
               'activation_url': request.build_absolute_uri(
                   reverse('account_confirm_email',
                           kwargs={'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                                   'token': token_generator.make_token(user)}))
               }

    send_templated_mail(
        'registration/email_confirmation',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        context=context)
