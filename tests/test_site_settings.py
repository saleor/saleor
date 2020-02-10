import pytest
from django.contrib.sites.models import Site
from django.db.utils import IntegrityError

from saleor.site import utils
from saleor.site.models import AuthorizationKey, SiteSettings


def test_get_authorization_key_for_backend(
    site_settings, authorization_key, authorization_backend_name
):
    key_for_backend = utils.get_authorization_key_for_backend(
        authorization_backend_name
    )
    assert key_for_backend == authorization_key


def test_get_authorization_key_no_settings_site(
    settings, authorization_key, authorization_backend_name
):
    settings.SITE_ID = None
    assert utils.get_authorization_key_for_backend(authorization_backend_name) is None


def test_one_authorization_key_for_backend_and_settings(
    site_settings, authorization_key, authorization_backend_name
):
    with pytest.raises(IntegrityError):
        AuthorizationKey.objects.create(
            site_settings=site_settings, name=authorization_backend_name
        )


def test_authorization_key_key_and_secret(authorization_key):
    assert authorization_key.key_and_secret() == ("Key", "Password")


def test_settings_available_backends_empty(site_settings):
    assert site_settings.available_backends().count() == 0


def test_settings_available_backends(site_settings, authorization_key):
    backend_name = authorization_key.name
    available_backends = site_settings.available_backends()
    assert backend_name in available_backends


def test_new_get_current():
    result = Site.objects.get_current()
    assert result.name == "mirumee.com"
    assert result.domain == "mirumee.com"
    assert type(result.settings) == SiteSettings
    assert str(result.settings) == "mirumee.com"
