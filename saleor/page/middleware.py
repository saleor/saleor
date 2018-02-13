from django.conf import settings
from django.http import Http404

from .views import page_detail


class PageFallbackMiddleware:

    def process_response(self, request, response):
        if response.status_code != 404:
            return response
        try:
            return page_detail(request, request.path_info)
        except Http404:
            return response
        except Exception:
            if settings.DEBUG:
                raise
            return response
