import pytest
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

from ..models import SiteSettings


def test_new_get_current():
    result = Site.objects.get_current()
    assert result.name == "example.com"
    assert result.domain == "example.com"
    assert type(result.settings) is SiteSettings


def test_site_settings_default_from_email(settings):
    site = Site.objects.get_current()
    site.settings.default_mail_sender_address = None
    assert site.settings.default_from_email == settings.DEFAULT_FROM_EMAIL
    settings.DEFAULT_FROM_EMAIL = None
    with pytest.raises(ImproperlyConfigured):
        _x = site.settings.default_from_email


@pytest.fixture
def cold_site_cache():
    """Bust the process-global site cache around a test that reads it.

    ``THREADED_SITE_CACHE`` survives between tests, so a test that primes it
    under one ``SITE_ID`` would otherwise answer a later lookup from the wrong
    entry.
    """
    Site.objects.clear_cache()
    yield
    Site.objects.clear_cache()


@pytest.mark.parametrize(
    ("_case", "host"),
    [
        ("host matches the domain exactly", "example.com"),
        ("host carries a port the domain does not", "example.com:8000"),
    ],
)
def test_new_get_current_without_site_id_resolves_by_host(
    _case, host, site_settings, settings, rf, cold_site_cache
):
    # given
    settings.SITE_ID = None
    expected_site = site_settings.site
    assert expected_site.domain == "example.com"
    assert expected_site.domain in settings.ALLOWED_HOSTS

    request = rf.get("/", headers={"host": host})
    assert request.get_host() == host

    # when
    site = Site.objects.get_current(request)

    # then
    assert site.pk == expected_site.pk
    assert site.domain == expected_site.domain
    assert type(site.settings) is SiteSettings


def test_new_get_current_without_site_id_unknown_host_raises_does_not_exist(
    settings, rf, cold_site_cache
):
    # given
    settings.SITE_ID = None
    host = "absent.test"
    settings.ALLOWED_HOSTS = [host]
    assert Site.objects.filter(domain__iexact=host).exists() is False
    request = rf.get("/", headers={"host": host})

    # when / then
    with pytest.raises(Site.DoesNotExist):
        Site.objects.get_current(request)


def test_new_get_current_unknown_site_id_raises_does_not_exist(
    settings, db, cold_site_cache
):
    # given
    missing_site_id = -1
    settings.SITE_ID = missing_site_id
    assert Site.objects.filter(pk=missing_site_id).exists() is False

    # when / then
    with pytest.raises(Site.DoesNotExist):
        Site.objects.get_current()


def test_new_get_by_natural_key_unknown_domain_raises_does_not_exist(db):
    # given
    domain = "absent.test"
    assert Site.objects.filter(domain__iexact=domain).exists() is False

    # when / then
    with pytest.raises(Site.DoesNotExist):
        Site.objects.get_by_natural_key(domain)


def test_new_get_by_natural_key_returns_the_site(site_settings):
    # given
    expected_site = site_settings.site

    # when
    site = Site.objects.get_by_natural_key(expected_site.domain.upper())

    # then
    assert site.pk == expected_site.pk
    assert type(site.settings) is SiteSettings
