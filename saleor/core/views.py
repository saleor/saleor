import os

from django.template.response import TemplateResponse
from django.conf import settings
from django.http import HttpResponseNotAllowed


def home(request):
    storefront_url = os.environ.get("STOREFRONT_URL", "")
    dashboard_url = os.environ.get("DASHBOARD_URL", "")
    if not settings.PLAYGROUND_ENABLED:
        return HttpResponseNotAllowed(["OPTIONS", "POST"])
    else:
        return TemplateResponse(
            request,
            "home/index.html",
            {"storefront_url": storefront_url, "dashboard_url": dashboard_url},
        )
