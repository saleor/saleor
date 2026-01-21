import logging
import os

from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.views.static import serve

from .jwt_manager import get_jwt_manager

logger = logging.getLogger(__name__)


def home(request):
    storefront_url = os.environ.get("STOREFRONT_URL", "")
    dashboard_url = os.environ.get("DASHBOARD_URL", "")
    return TemplateResponse(
        request,
        "home/index.html",
        {"storefront_url": storefront_url, "dashboard_url": dashboard_url},
    )


def jwks(request):
    return JsonResponse(get_jwt_manager().get_jwks())


def serve_media_view(
    request: HttpRequest, *args, **kwargs
) -> HttpResponse | FileResponse:
    """Serve media files and other user-uploaded media files from local storage.

    WARNING: just like Django's built-in ``django.views.static.serve()`` view:
             this view is not suitable for production use. This view is only meant
             for development purposes and convenience, as well as to show how
             production workloads are expected to behave.

             Learn more about static views: https://docs.djangoproject.com/en/5.2/howto/static-files/#serving-static-files-during-development

    This view wraps ``django.views.static.serve()`` in order to add
    a ``Content-Disposition: attachment`` header due to not exposing a setting to
    control the response headers.

    This is not intended to protect users in production workloads, instead users
    should configure their servers (CDN or reverse-proxy) to host the media files
    and to return the ``Content-Disposition: attachment`` header; this only for
    demonstrating the expected behavior.
    """

    # Not allowed when DEBUG=False
    if not settings.DEBUG:
        raise Http404

    response: HttpResponse | FileResponse = serve(request, *args, **kwargs)

    # When serving files, force clients to download the file instead of Django's
    # default value 'Content-Disposition: inline' which indicates to the clients
    # that they can display the value.
    if isinstance(response, FileResponse):
        response.headers["Content-Disposition"] = "attachment"
    return response
