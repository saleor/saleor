import pytest
from django.core.exceptions import ImproperlyConfigured

from ..emails import get_email_context


def test_get_email_context(site_settings):
    site = site_settings.site

    expected_send_kwargs = {"from_email": site_settings.default_from_email}
    proper_context = {
        "domain": site.domain,
        "site_name": site.name,
    }

    send_kwargs, received_context = get_email_context()
    assert send_kwargs == expected_send_kwargs
    assert proper_context == received_context


def test_email_having_display_name_in_settings(customer_user, site_settings, settings):
    expected_from_email = "Info <hello@mirumee.com>"

    site_settings.default_mail_sender_name = None
    site_settings.default_mail_sender_address = None

    settings.DEFAULT_FROM_EMAIL = expected_from_email

    assert site_settings.default_from_email == expected_from_email


def test_email_with_email_not_configured_raises_error(settings, site_settings):
    """Ensure an exception is thrown when not default sender is set;
    both missing in the settings.py and in the site settings table.
    """
    site_settings.default_mail_sender_address = None
    settings.DEFAULT_FROM_EMAIL = None

    with pytest.raises(ImproperlyConfigured) as exc:
        _ = site_settings.default_from_email

    assert exc.value.args == ("No sender email address has been set-up",)
