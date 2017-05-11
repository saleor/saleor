from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from saleor_oye import models as oye_models
from saleor_oye.utils import visible_products

from saleor.elasticsearch.search import Release, Artist

__author__ = 'tkolter'


def bulk_indexing_releases():
    Release.init()
    es = Elasticsearch()
    bulk(
        client=es,
        actions=(b.indexing() for b in visible_products())
    )


def bulk_indexing_artists():
    Artist.init()
    es = Elasticsearch()
    bulk(
        client=es,
        actions=(b.indexing() for b in oye_models.Artist.objects.all())
    )
