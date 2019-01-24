# import pytest
#
# from django.core.urlresolvers import reverse
# from django.utils.encoding import smart_text
#
# from saleor.site.models import SiteSettings
# from saleor.site import utils
# from saleor.dashboard.sites.forms import SiteSettingForm
#
#
# @pytest.fixture
# def site_settings(db, settings):
#     obj = SiteSettings.objects.create(name="mirumee.com",
#                                       header_text="mirumee.com",
#                                       domain="mirumee.com")
#     settings.SITE_SETTINGS_ID = obj.pk
#     return obj
#
#
# def test_get_site_settings_uncached(site_settings):
#     result = utils.get_site_settings_uncached(site_settings.id)
#     assert result == site_settings
#
#
# def test_index_view(admin_client, site_settings):
#     response = admin_client.get(reverse('dashboard:site-index'), follow=True)
#     assert response.status_code == 200
#
#     context = response.context
#     assert context['site'] == site_settings
#
#
# @pytest.mark.django_db
# def test_form():
#     data = {'name': 'mirumee', 'domain': 'mirumee.com'}
#     form = SiteSettingForm(data)
#     assert form.is_valid()
#
#     site = form.save()
#     assert smart_text(site) == 'mirumee'
#
#     form = SiteSettingForm({})
#     assert not form.is_valid()
#
#
# def test_site_update_view(admin_client, site_settings):
#     url = reverse('dashboard:site-update',
#                   kwargs={'site_id': site_settings.id})
#     response = admin_client.get(url)
#     assert response.status_code == 200
#
#     data = {'name': 'Mirumee Labs', 'header_text': 'We have all the things!',
#             'domain': 'mirumee.com'}
#     response = admin_client.post(url, data)
#     assert response.status_code == 200
#
#     site_settings.refresh_from_db()
#     assert site_settings.name == 'Mirumee Labs'
