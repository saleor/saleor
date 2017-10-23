from django.urls import reverse

from saleor.site.utils import get_site_settings


def test_sitemap_uses_site_settings_domain(client, product_in_stock):
    url = 'http://%(domain)s%(product_url)s' % {
        'domain': get_site_settings().domain,
        'product_url': product_in_stock.get_absolute_url()}
    response = client.get(reverse('django.contrib.sitemaps.views.sitemap'))
    assert response.context['urlset'][0]['location'] == url
