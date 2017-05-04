from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from saleor_oye.models import Artikel
from saleor_oye.utils import visible_products

from saleor.elasticsearch.search import Release

__author__ = 'tkolter'


def bulk_indexing():
    Release.init()
    es = Elasticsearch()
    bulk(
        client=es,
        actions=(b.indexing() for b in visible_products())
    )
