from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from ...settings import DEFAULT_FROM_EMAIL, get_host


def send_set_password_email(staff):
    ctx = {
        'email': staff.email,
        'domain': get_host(),
        'site_name': 'saleor',
        'uid': urlsafe_base64_encode(force_bytes(staff.pk)),
        'user': staff,
        'token': default_token_generator.make_token(staff),
        'protocol': 'http',
    }
    subject_template_name = 'account/email/password_reset_subject.txt'
    email_template_name = 'account/email/password_reset_message.txt'
    subject = loader.render_to_string(subject_template_name, ctx)
    subject = ''.join(subject.splitlines())
    email = loader.render_to_string(email_template_name, ctx)
    send_mail(subject, email, DEFAULT_FROM_EMAIL, [staff.email],
              fail_silently=False)
