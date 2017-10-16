from django.urls import reverse

from saleor.site.utils import get_site_settings


def test_sitemap_uses_site_settings_domain(client, product_in_stock):
    site_settings = get_site_settings()
    site_settings.domain = 'my-domain.com'
    site_settings.save()
    absolute_url = 'http://%s%s' % (
        site_settings.domain, product_in_stock.get_absolute_url())
    response = client.get(reverse('django.contrib.sitemaps.views.sitemap'))
    assert response.context['urlset'][0]['location'] == absolute_url
