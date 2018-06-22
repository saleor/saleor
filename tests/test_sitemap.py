from django.conf import settings
from django.urls import reverse, translate_url

from saleor.core.utils import build_absolute_uri


def test_sitemap(client, product):
    product_url = build_absolute_uri(product.get_absolute_url())
    category_url = build_absolute_uri(
        product.category.get_absolute_url())
    expected_urls = [product_url, category_url]

    language_codes = [lang_code for lang_code, lang_name in settings.LANGUAGES]
    expected_urls_i18n = [
        translate_url(url, language_code)
        for url in expected_urls
        for language_code in language_codes]
    response = client.get(reverse('django.contrib.sitemaps.views.sitemap'))
    sitemap_links = [url['location'] for url in response.context['urlset']]
    assert sorted(sitemap_links) == sorted(expected_urls_i18n)
