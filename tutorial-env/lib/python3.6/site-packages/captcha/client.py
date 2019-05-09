import json

from django.conf import settings

from captcha._compat import (
    build_opener, ProxyHandler, PY2, Request, urlencode, urlopen, want_bytes
)
from captcha.decorators import generic_deprecation

DEFAULT_API_SSL_SERVER = "//www.google.com/recaptcha/api"  # made ssl agnostic
DEFAULT_API_SERVER = "//www.google.com/recaptcha/api"  # made ssl agnostic
DEFAULT_VERIFY_SERVER = "www.google.com"
if getattr(settings, "NOCAPTCHA", False):
    DEFAULT_WIDGET_TEMPLATE = 'captcha/widget_nocaptcha.html'
else:
    DEFAULT_WIDGET_TEMPLATE = 'captcha/widget.html'
DEFAULT_WIDGET_TEMPLATE_AJAX = 'captcha/widget_ajax.html'

API_SSL_SERVER = getattr(settings, "CAPTCHA_API_SSL_SERVER",
                         DEFAULT_API_SSL_SERVER)
API_SERVER = getattr(settings, "CAPTCHA_API_SERVER", DEFAULT_API_SERVER)
VERIFY_SERVER = getattr(settings, "CAPTCHA_VERIFY_SERVER",
                        DEFAULT_VERIFY_SERVER)

if getattr(settings, "CAPTCHA_AJAX", False):
    WIDGET_TEMPLATE = getattr(settings, "CAPTCHA_WIDGET_TEMPLATE",
                              DEFAULT_WIDGET_TEMPLATE_AJAX)
else:
    WIDGET_TEMPLATE = getattr(settings, "CAPTCHA_WIDGET_TEMPLATE",
                              DEFAULT_WIDGET_TEMPLATE)


RECAPTCHA_SUPPORTED_LANUAGES = ('en', 'nl', 'fr', 'de', 'pt', 'ru', 'es', 'tr')


class RecaptchaResponse(object):
    def __init__(self, is_valid, error_code=None):
        self.is_valid = is_valid
        self.error_code = error_code


def request(*args, **kwargs):
    """
    Make a HTTP request with a proxy if configured.
    """
    if getattr(settings, 'RECAPTCHA_PROXY', False):
        proxy = ProxyHandler({
            'http': settings.RECAPTCHA_PROXY,
            'https': settings.RECAPTCHA_PROXY,
        })
        opener = build_opener(proxy)

        return opener.open(*args, **kwargs)
    else:
        return urlopen(*args, **kwargs)


@generic_deprecation(
    "reCAPTCHA v1 will no longer be supported."
    " See NOCAPTCHA settings documentation and ensure the value is set to True."
)
def submit(recaptcha_challenge_field,
           recaptcha_response_field,
           private_key,
           remoteip,
           use_ssl=False):
    """
    Submits a reCAPTCHA request for verification. Returns RecaptchaResponse
    for the request

    recaptcha_challenge_field -- The value of recaptcha_challenge_field
    from the form
    recaptcha_response_field -- The value of recaptcha_response_field
    from the form
    private_key -- your reCAPTCHA private key
    remoteip -- the user's ip address
    """

    if not (recaptcha_response_field and recaptcha_challenge_field and
            len(recaptcha_response_field) and len(recaptcha_challenge_field)):
        return RecaptchaResponse(
            is_valid=False,
            error_code='incorrect-captcha-sol'
        )

    if getattr(settings, "NOCAPTCHA", False):
        params = urlencode({
            'secret': want_bytes(private_key),
            'response': want_bytes(recaptcha_response_field),
            'remoteip': want_bytes(remoteip),
        })
    else:
        params = urlencode({
            'privatekey': want_bytes(private_key),
            'remoteip':  want_bytes(remoteip),
            'challenge':  want_bytes(recaptcha_challenge_field),
            'response':  want_bytes(recaptcha_response_field),
        })

    if not PY2:
        params = params.encode('utf-8')

    if use_ssl:
        verify_url = 'https://%s/recaptcha/api/verify' % VERIFY_SERVER
    else:
        verify_url = 'http://%s/recaptcha/api/verify' % VERIFY_SERVER

    if getattr(settings, "NOCAPTCHA", False):
        verify_url = 'https://%s/recaptcha/api/siteverify' % VERIFY_SERVER

    req = Request(
        url=verify_url,
        data=params,
        headers={
            'Content-type': 'application/x-www-form-urlencoded',
            'User-agent': 'reCAPTCHA Python'
        }
    )

    httpresp = request(req)
    if getattr(settings, "NOCAPTCHA", False):
        data = json.loads(httpresp.read().decode('utf-8'))
        return_code = data['success']
        return_values = [return_code, None]
        if return_code:
            return_code = 'true'
        else:
            return_code = 'false'
    else:
        return_values = httpresp.read().decode('utf-8').splitlines()
        return_code = return_values[0]

    httpresp.close()

    if (return_code == "true"):
        return RecaptchaResponse(is_valid=True)
    else:
        return RecaptchaResponse(is_valid=False, error_code=return_values[1])
