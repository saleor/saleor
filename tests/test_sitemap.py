from django.contrib.sites.models import Site
from django.urls import reverse


def test_sitemap_uses_site_settings_domain(client, product_in_stock):
    domain = Site.objects.get_current().domain
    product_url = 'http://%(domain)s%(product_url)s' % {
        'domain': domain,
        'product_url': product_in_stock.get_absolute_url()}
    category_url = 'http://%(domain)s%(category_url)s' % {
        'domain': domain,
        'category_url': product_in_stock.category.get_absolute_url()}
    expected_links = [product_url, category_url]

    response = client.get(reverse('django.contrib.sitemaps.views.sitemap'))
    sitemap_links = [url['location'] for url in response.context['urlset']]
    assert sorted(sitemap_links) == sorted(expected_links)
