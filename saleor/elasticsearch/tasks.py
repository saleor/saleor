from celery import shared_task
from saleor_oye.models import Artist, Artikel, WebShopRelease

__author__ = 'tkolter'


@shared_task()
def indexing_artist(pk):
    try:
        artist = Artist.objects.get(pk=pk)
        artist.indexing()
    except Artist.DoesNotExist:
        pass


@shared_task()
def indexing_release(pk):
    try:
        release = Artikel.objects.get(pk=pk)
        release.indexing()
    except Artikel.DoesNotExist:
        pass


@shared_task()
def index_missing_releases():
    for wsr in WebShopRelease.objects.filter(has_elastic_index__isnull=True):
        wsr.release.indexing()
