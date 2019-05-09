import os
import sys
import socket

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from . import client
from .constants import TEST_PUBLIC_KEY, TEST_PRIVATE_KEY
from .widgets import ReCaptcha, ReCaptchaV2Invisible


class ReCaptchaField(forms.CharField):
    default_error_messages = {
        'captcha_invalid': _('Incorrect, please try again.'),
        'captcha_error': _('Error verifying input, please try again.'),
    }

    def __init__(self, public_key=None, private_key=None, use_ssl=None,
                 attrs=None, *args, **kwargs):
        """
        ReCaptchaField can accepts attributes which is a dictionary of
        attributes to be passed to the ReCaptcha widget class. The widget will
        loop over any options added and create the RecaptchaOptions
        JavaScript variables as specified in
        https://developers.google.com/recaptcha/docs/display#render_param
        """
        if attrs is None:
            attrs = {}
        public_key = public_key if public_key else \
            getattr(settings, 'RECAPTCHA_PUBLIC_KEY', TEST_PUBLIC_KEY)
        self.private_key = private_key if private_key else \
            getattr(settings, 'RECAPTCHA_PRIVATE_KEY', TEST_PRIVATE_KEY)
        self.use_ssl = use_ssl if use_ssl is not None else getattr(
            settings, 'RECAPTCHA_USE_SSL', True)

        # TODO: Widget selection to be cleaned up along with v1 removal.
        if getattr(settings, 'RECAPTCHA_V2_INVISIBLE', False):
            self.widget = ReCaptchaV2Invisible(public_key=public_key, attrs=attrs)
        else:
            self.widget = ReCaptcha(public_key=public_key, attrs=attrs)
        self.required = True
        super(ReCaptchaField, self).__init__(*args, **kwargs)

    def get_remote_ip(self):
        f = sys._getframe()
        while f:
            if 'request' in f.f_locals:
                request = f.f_locals['request']
                if request:
                    remote_ip = request.META.get('REMOTE_ADDR', '')
                    forwarded_ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
                    ip = remote_ip if not forwarded_ip else forwarded_ip
                    return ip
            f = f.f_back

    def clean(self, values):
        super(ReCaptchaField, self).clean(values[1])
        recaptcha_challenge_value = force_text(values[0])
        recaptcha_response_value = force_text(values[1])

        if not self.required:
            return

        try:
            check_captcha = client.submit(
                recaptcha_challenge_value,
                recaptcha_response_value, private_key=self.private_key,
                remoteip=self.get_remote_ip(), use_ssl=self.use_ssl)

        # TODO: Does not catch urllib2.HTTPError correctly
        except socket.error:  # Catch timeouts, etc
            raise ValidationError(
                self.error_messages['captcha_error']
            )

        if not check_captcha.is_valid:
            raise ValidationError(
                self.error_messages['captcha_invalid']
            )
        return values[0]
