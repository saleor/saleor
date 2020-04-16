import os

from django.template.response import TemplateResponse


def home(request):
    storefront = os.environ.get("STOREFRONT_URL", "")
    dashboard = os.environ.get("DASHBOARD_URL", "")
    return TemplateResponse(
        request, "home.html", {"storefront": storefront, "dashboard": dashboard}
    )
