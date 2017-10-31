from __future__ import unicode_literals

from elasticsearch import Elasticsearch
from django.utils.six.moves.urllib.parse import urlparse
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch

# module scoped elasticsearch client handler for dependency injection
CLIENT = Elasticsearch()


def search_products(phrase):
    ''' Execute external search for product matching phrase  '''
    INDEX = 'storefront__product_product'  # TODO: parametrize this
    CONTENT = 'product.Product'
    query = MultiMatch(fields=['name', 'description'], query=phrase)
    search = (Search(index=INDEX).query(query)
                                 .source(['pk'])
                                 .using(CLIENT)
                                 .filter('match', content_type=CONTENT))
    return [hit.pk for hit in search.execute()]


def _make_host_entry(url):
    use_ssl = url.scheme == 'https'
    auth = (url.username, url.password)
    http_auth = auth if all(auth) else None
    return {
        'host': url.hostname,
        'port': url.port or (443 if use_ssl else 80),
        'url_prefix': url.path,
        'use_ssl': use_ssl,
        'verify_certs': use_ssl,
        'http_auth': http_auth
    }


def _get_es_hosts(params):
    hosts = params.pop('HOSTS', [])
    es_urls = map(urlparse, params.pop('URLS', []))
    return hosts + [_make_host_entry(url) for url in es_urls]


class SearchBackend(object):
    rebuilder_class = None

    def __init__(self, params):
        global CLIENT
        CLIENT = Elasticsearch(hosts=_get_es_hosts(params))

    def search(self, query, model_or_queryset):
        return model_or_queryset.filter(pk__in=search_products(query))
