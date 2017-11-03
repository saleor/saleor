from __future__ import unicode_literals

from elasticsearch import Elasticsearch
from django.utils.six.moves.urllib.parse import urlparse
from django.db.models.query import QuerySet
from elasticsearch_dsl.query import MultiMatch
from ..documents import ProductDocument


def _make_host_entry(url):
    use_ssl = url.scheme == 'https'
    auth = (url.username, url.password)
    return {
        'host': url.hostname,
        'port': url.port or (443 if use_ssl else 80),
        'url_prefix': url.path,
        'use_ssl': use_ssl,
        'verify_certs': use_ssl,
        'http_auth': auth if all(auth) else None
    }


def _get_es_hosts(params):
    hosts = params.pop('HOSTS', [])
    es_urls = map(urlparse, params.pop('URLS', []))
    return hosts + [_make_host_entry(url) for url in es_urls]


class SearchBackend(object):
    rebuilder_class = None
    client = None

    @staticmethod
    def search(query, model_or_queryset):
        qs = model_or_queryset
        # TODO: remove this ugly type incoherence of old search api
        if not isinstance(model_or_queryset, QuerySet):
            qs = model_or_queryset.objects.all()
        return qs.filter(pk__in=search_products(query))


def search_products(phrase):
    ''' Execute external search for product matching phrase  '''
    query = MultiMatch(fields=['name', 'description'], query=phrase)
    search = (ProductDocument.search()
                             .query(query)
                             .source(False)
                             .filter('term', is_published=True))
    return [hit.meta.id for hit in search.execute()]
