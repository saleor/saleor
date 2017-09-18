from celery import shared_task
from saleor_oye.models import Artist

__author__ = 'tkolter'


@shared_task()
def indexing_artist(pk):
    try:
        artist = Artist.objects.get(pk=pk)
        artist.indexing()
    except Artist.DoesNotExist:
        pass
