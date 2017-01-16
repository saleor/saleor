import pytest

from django.core.urlresolvers import reverse
from django.utils.encoding import smart_text

from saleor.site.models import SiteSetting
from saleor.site import utils
from saleor.dashboard.sites.forms import SiteSettingForm
from .utils import get_redirect_location


@pytest.fixture
def site_settings(db):
    return SiteSetting.objects.create(name="mirumee.com", domain="mirumee.com")


def test_get_site_settings_uncached(site_settings):
    result = utils.get_site_settings_uncached(site_settings.id)
    assert result == site_settings


def test_index_view(admin_client, site_settings):
    response = admin_client.get(reverse('dashboard:site-index'))
    assert response.status_code == 200

    context = response.context
    assert list(context['sites']) == [site_settings]


@pytest.mark.django_db
def test_form():
    data = {'name': 'mirumee', 'domain': 'mirumee.com'}
    form = SiteSettingForm(data)
    assert form.is_valid()

    site = form.save()
    assert smart_text(site) == 'mirumee'

    form = SiteSettingForm({})
    assert not form.is_valid()


def test_create_view(admin_client):
    url = reverse('dashboard:site-create')
    response = admin_client.get(url)
    assert response.status_code == 200

    site_count = SiteSetting.objects.count()
    data = {'name': 'mirumee', 'domain': 'mirumee.com'}
    response_post = admin_client.post(url, data)
    assert response_post.status_code == 302

    redirect_location = get_redirect_location(response_post)
    assert redirect_location == reverse('dashboard:site-index')

    assert SiteSetting.objects.count() == site_count + 1


def test_site_update_view(admin_client, site_settings):
    url = reverse('dashboard:site-update',
                  kwargs={'site_id': site_settings.id})
    response = admin_client.get(url)
    assert response.status_code == 200

    data = {'name': 'Mirumee Labs', 'domain': 'mirumee.com'}
    response = admin_client.post(url, data)
    assert response.status_code == 200

    site_settings.refresh_from_db()
    assert site_settings.name == 'Mirumee Labs'
