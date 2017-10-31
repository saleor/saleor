from elasticsearch import Elasticsearch
from django.utils.six.moves.urllib.parse import urlparse
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch

from ...product.models import Product


CLIENT = Elasticsearch()


def search(phrase):
    result = (Search()
              .query(MultiMatch(query=phrase, fields=['name', 'description']))
              .source(['pk'])
              .using(CLIENT)
              .execute())
    return [hit.pk for hit in result]


def _get_es_hosts(params):
    hosts = params.pop('HOSTS', None) or []
    es_urls = params.pop('URLS', ['http://localhost:9200'])
    for url in es_urls:
        parsed_url = urlparse(url)
        use_ssl = parsed_url.scheme == 'https'
        port = parsed_url.port or (443 if use_ssl else 80)
        http_auth = None
        if parsed_url.username and parsed_url.password:
            http_auth = (parsed_url.username, parsed_url.password)
        hosts.append({
            'host': parsed_url.hostname,
            'port': port,
            'url_prefix': parsed_url.path,
            'use_ssl': use_ssl,
            'verify_certs': use_ssl,
            'http_auth': http_auth})
    return hosts


class SearchBackend(object):
    rebuilder_class = None

    def __init__(self, params):
        global CLIENT
        CLIENT = Elasticsearch(hosts=_get_es_hosts(params))

    def search(self, query, model_or_queryset=None):
        found_product_ids = search(query)
        products = Product.objects.filter(pk__in=found_product_ids)
        return [str(obj.pk) for obj in products]
