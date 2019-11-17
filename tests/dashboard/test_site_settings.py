import pytest
from django.contrib.sites.models import Site
from django.db.utils import IntegrityError
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.encoding import smart_text

from saleor.dashboard.sites.forms import SiteForm, SiteSettingsForm
from saleor.site import utils
from saleor.site.models import AuthorizationKey, SiteSettings


@pytest.fixture
def site_settings_form_data():
    return {
        "header_text": "mirumee",
        "description": "mirumee.com",
        "default_weight_unit": "lb",
    }


def test_index_view(admin_client, site_settings):
    response = admin_client.get(reverse("dashboard:site-index"), follow=True)
    assert response.status_code == 200

    context = response.context
    assert context["site_settings"] == site_settings


def test_site_form():
    data = {"name": "mirumee_test", "domain": "mirumee_test.com"}
    form = SiteForm(data)
    assert form.is_valid()
    site = form.save()
    assert smart_text(site) == "mirumee_test.com"
    form = SiteForm({})
    assert not form.is_valid()


def test_site_settings_form(site_settings, site_settings_form_data):
    data = site_settings_form_data
    form = SiteSettingsForm(data, instance=site_settings)
    assert form.is_valid()

    site = form.save()
    assert site.header_text == "mirumee"
    assert smart_text(site) == "mirumee.com"
    assert site.default_weight_unit == "lb"

    form = SiteSettingsForm({"default_weight_unit": "lb"})
    assert form.is_valid()


@pytest.mark.parametrize(
    "sender_name, sender_address, expected_errors",
    (
        (
            "hello\nworld",
            "hello@example.com\n",
            {"default_mail_sender_name": ["New lines are not allowed."]},
        ),
        (
            "hello\rworld",
            "hello@example.com",
            {"default_mail_sender_name": ["New lines are not allowed."]},
        ),
        (
            "\rhello world\r",
            "hello@example.co\rm",
            {"default_mail_sender_address": ["Enter a valid email address."]},
        ),
    ),
)
def test_site_settings_default_sender_name_cannot_have_newlines(
    site_settings_form_data, sender_name, sender_address, expected_errors
):
    data = site_settings_form_data
    data.update(
        {
            "default_mail_sender_name": sender_name,
            "default_mail_sender_address": sender_address,
        }
    )
    form = SiteSettingsForm(data)
    assert not form.is_valid()
    assert form.errors == expected_errors


def test_site_update_view(admin_client, site_settings):
    url = reverse("dashboard:site-update", kwargs={"pk": site_settings.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    data = {
        "name": "Mirumee Labs",
        "header_text": "We have all the things!",
        "domain": "newmirumee.com",
        "default_weight_unit": "lb",
        "form-TOTAL_FORMS": 0,
        "form-INITIAL_FORMS": 0,
        "default_mail_sender_name": "Mirumee Labs Info",
        "default_mail_sender_address": "hello@example.com",
    }
    response = admin_client.post(url, data)
    assert response.status_code == 302

    site_settings: SiteSettings = SiteSettings.objects.get(pk=site_settings.id)
    assert site_settings.header_text == "We have all the things!"
    assert site_settings.default_weight_unit == "lb"
    assert site_settings.site.domain == "newmirumee.com"
    assert site_settings.site.name == "Mirumee Labs"
    assert site_settings.default_mail_sender_name == "Mirumee Labs Info"
    assert site_settings.default_mail_sender_address == "hello@example.com"
    assert site_settings.default_from_email == "Mirumee Labs Info <hello@example.com>"


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


def test_authorization_key_form_add(admin_client, site_settings):
    assert site_settings.available_backends().count() == 0
    data = {
        "site_settings": site_settings.pk,
        "name": "google-oauth2",
        "key": "key",
        "password": "password",
    }
    url = reverse(
        "dashboard:authorization-key-add", kwargs={"site_settings_pk": site_settings.pk}
    )
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert AuthorizationKey.objects.count() == 1
    assert site_settings.available_backends().count() == 1
    assert "google-oauth2" in site_settings.available_backends()


def test_authorization_key_form_add_not_valid(admin_client, site_settings):
    assert site_settings.available_backends().count() == 0
    data = {
        "site_settings": "not_valid",
        "name": "not_valid",
        "key": "key",
        "password": "",
    }
    url = reverse(
        "dashboard:authorization-key-add", kwargs={"site_settings_pk": site_settings.pk}
    )
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert AuthorizationKey.objects.count() == 0
    assert site_settings.available_backends().count() == 0


def test_authorization_key_form_edit(admin_client, site_settings, authorization_key):
    assert site_settings.available_backends().count() == 1
    data = {
        "site_settings": site_settings.pk,
        "name": "google-oauth2",
        "key": "key",
        "password": "password",
    }
    url = reverse(
        "dashboard:authorization-key-edit",
        kwargs={"site_settings_pk": site_settings.pk, "key_pk": authorization_key.pk},
    )
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert AuthorizationKey.objects.count() == 1
    assert site_settings.available_backends().count() == 1
    assert "google-oauth2" in site_settings.available_backends()


def test_authorization_key_form_delete(admin_client, site_settings, authorization_key):
    assert site_settings.available_backends().count() == 1
    url = reverse(
        "dashboard:authorization-key-delete",
        kwargs={"site_settings_pk": site_settings.pk, "key_pk": authorization_key.pk},
    )
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert AuthorizationKey.objects.count() == 0
    assert site_settings.available_backends().count() == 0


def test_new_get_current():
    result = Site.objects.get_current()
    assert result.name == "mirumee.com"
    assert result.domain == "mirumee.com"
    assert type(result.settings) == SiteSettings
    assert str(result.settings) == "mirumee.com"


def test_new_get_current_from_request():
    factory = RequestFactory()
    request = factory.get(reverse("dashboard:site-index"))
    result = Site.objects.get_current(request)
    assert result.name == "mirumee.com"
    assert result.domain == "mirumee.com"
    assert type(result.settings) == SiteSettings
    assert str(result.settings) == "mirumee.com"
