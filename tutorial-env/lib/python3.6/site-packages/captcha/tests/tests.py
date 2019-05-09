import os
import warnings

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from captcha import fields
from django.forms import Form
from django.test import TestCase, override_settings

from captcha.client import RecaptchaResponse


class TestForm(Form):
    captcha = fields.ReCaptchaField(attrs={'theme': 'white'})


class TestCase(TestCase):
    # No longer supports reCAPTCHA v1, override settings during tests to always
    # use v2 reCAPTCHA. Prevents HTTP 410 error.
    @override_settings(NOCAPTCHA=True)
    @patch("captcha.fields.client.submit")
    def test_client_success_response(self, mocked_submit):
        mocked_submit.return_value = RecaptchaResponse(is_valid=True)
        form_params = {'recaptcha_response_field': 'PASSED'}
        form = TestForm(form_params)
        self.assertTrue(form.is_valid())

    # No longer supports reCAPTCHA v1, override settings during tests to always
    # use v2 reCAPTCHA. Prevents HTTP 410 error.
    @override_settings(NOCAPTCHA=True)
    @patch("captcha.fields.client.submit")
    def test_client_failure_response(self, mocked_submit):
        mocked_submit.return_value = RecaptchaResponse(is_valid=False, error_code="410")
        form_params = {'recaptcha_response_field': 'PASSED'}
        form = TestForm(form_params)
        self.assertFalse(form.is_valid())

    # No longer supports reCAPTCHA v1, override settings during tests to always
    # use v2 reCAPTCHA. Prevents HTTP 410 error.
    @override_settings(NOCAPTCHA=True)
    def test_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            form_params = {'recaptcha_response_field': 'PASSED'}
            form = TestForm(form_params)

            # Trigger warning on client.submit
            form.is_valid()
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "reCAPTCHA v1 will no longer be" in str(w[-1].message)
