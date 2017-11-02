from django.contrib.sites.models import Site
from django.urls import reverse


def test_sitemap_uses_site_settings_domain(client, product_in_stock):
    url = 'http://%(domain)s%(product_url)s' % {
        'domain': Site.objects.get_current().domain,
        'product_url': product_in_stock.get_absolute_url()}
    response = client.get(reverse('django.contrib.sitemaps.views.sitemap'))
    assert response.context['urlset'][0]['location'] == url
