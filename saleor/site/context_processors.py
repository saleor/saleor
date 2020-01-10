from typing import TYPE_CHECKING

from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import prefetch_related_objects

if TYPE_CHECKING:
    from django.http.request import HttpRequest


def site(request: "HttpRequest") -> dict:
    """Add site settings to the context under the 'site' key."""
    site = get_current_site(request)
    if isinstance(site, Site):
        prefetch_related_objects([site], "settings__translations")
    return {"site": site}
