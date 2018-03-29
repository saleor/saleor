from urllib.parse import urljoin

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from ...core.utils import build_absolute_uri


def get_webpage_schema(request):
    """Build a schema.org representation of the website."""
    site = get_current_site(request)
    url = build_absolute_uri(location='/')
    data = {
        '@context': 'http://schema.org',
        '@type': 'WebSite',
        'url': url,
        'name': site.name,
        'description': site.settings.description}
    if settings.ENABLE_SEARCH:
        search_url = urljoin(url, reverse('search:search'))
        data['potentialAction'] = {
            '@type': 'SearchAction',
            'target': '%s?q={q}' % search_url,
            'query-input': 'required name=q'}
    return data
