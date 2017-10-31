from elasticsearch import Elasticsearch
from django.utils.six.moves.urllib.parse import urlparse
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch

CLIENT = Elasticsearch()


def search_products(phrase):
    query = MultiMatch(fields=['name', 'description'], query=phrase)
    result = (Search(index='storefront__product_product').query(query)
                                                         .source(['pk'])
                                                         .using(CLIENT)
                                                         .execute())
    return [hit.pk for hit in result]


def _get_es_hosts(params):
    hosts = params.pop('HOSTS', [])
    es_urls = params.pop('URLS', [])
    for url in map(urlparse, es_urls):
        use_ssl = url.scheme == 'https'
        auth = (url.username, url.password)
        http_auth = auth if all(auth) else None
        hosts.append({
            'host': url.hostname,
            'port': url.port or (443 if use_ssl else 80),
            'url_prefix': url.path,
            'use_ssl': use_ssl,
            'verify_certs': use_ssl,
            'http_auth': http_auth
        })
    return hosts


class SearchBackend(object):
    rebuilder_class = None

    def __init__(self, params):
        global CLIENT
        CLIENT = Elasticsearch(hosts=_get_es_hosts(params))

    def search(self, query, model_or_queryset):
        return model_or_queryset.filter(pk__in=search_products(query))
