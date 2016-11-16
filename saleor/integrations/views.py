from __future__ import unicode_literals

from django.core.files.storage import default_storage
from django.http import Http404
from django.http import HttpResponse

from .feeds import SaleorFeed


def get_integration_response(file_path, content_type):
    if not default_storage.exists(file_path):
        raise Http404("Integration file does not exists")
    feed_file = default_storage.open(file_path)
    return HttpResponse(feed_file, content_type=content_type)


def saleor_feed(request):
    feed = SaleorFeed()
    return get_integration_response(feed.file_path,
                                    'application/atom+xml; charset=utf-8')
