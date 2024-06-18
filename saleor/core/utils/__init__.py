import socket
from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional, Union
from urllib.parse import urljoin, urlparse

from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Model
from django.utils.encoding import iri_to_uri
from django.utils.text import slugify
from text_unidecode import unidecode

if TYPE_CHECKING:
    from ...attribute.models import Attribute

task_logger = get_task_logger(__name__)


if TYPE_CHECKING:
    from django.utils.safestring import SafeText


def get_domain(site: Optional[Site] = None) -> str:
    if settings.PUBLIC_URL:
        return urlparse(settings.PUBLIC_URL).netloc
    if site is None:
        site = Site.objects.get_current()
    return site.domain


def get_public_url(domain: Optional[str] = None) -> str:
    if settings.PUBLIC_URL:
        return settings.PUBLIC_URL
    host = domain or Site.objects.get_current().domain
    protocol = "https" if settings.ENABLE_SSL else "http"
    return f"{protocol}://{host}"


def is_ssl_enabled() -> bool:
    if settings.PUBLIC_URL:
        return urlparse(settings.PUBLIC_URL).scheme.lower() == "https"
    return settings.ENABLE_SSL


def build_absolute_uri(location: str, domain: Optional[str] = None) -> str:
    """Create absolute uri from location.

    If provided location is absolute uri by itself, it returns unchanged value,
    otherwise if provided location is relative, absolute uri is built and returned.
    """
    current_uri = get_public_url(domain)
    location = urljoin(current_uri, location)
    return iri_to_uri(location)


def get_client_ip(request):
    """Retrieve the IP address from the request data.

    Tries to get a valid IP address from X-Forwarded-For, if the user is hiding behind
    a transparent proxy or if the server is behind a proxy.

    If no forwarded IP was provided or all of them are invalid,
    it fallback to the requester IP.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ips = ip.split(",")
    for ip in ips:
        if is_valid_ipv4(ip) or is_valid_ipv6(ip):
            return ip
    return request.META.get("REMOTE_ADDR", None)


def is_valid_ipv4(ip: str) -> bool:
    """Check whether the passed IP is a valid V4 IP address."""
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except OSError:
        return False
    return True


def is_valid_ipv6(ip: str) -> bool:
    """Check whether the passed IP is a valid V6 IP address."""
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except OSError:
        return False
    return True


def generate_unique_slug(
    instance: Model,
    slugable_value: str,
    slug_field_name: str = "slug",
    *,
    additional_search_lookup=None,
) -> str:
    """Create unique slug for model instance.

    The function uses `django.utils.text.slugify` to generate a slug from
    the `slugable_value` of model field. If the slug already exists it adds
    a numeric suffix and increments it until a unique value is found.

    Args:
        instance: model instance for which slug is created
        slugable_value: value used to create slug
        slug_field_name: name of slug field in instance model
        additional_search_lookup: when provided, it will be used to find the instances
            with the same slug that passed also additional conditions

    """
    slug = slugify(unidecode(slugable_value))

    # in case when slugable_value contains only not allowed in slug characters, slugify
    # function will return empty string, so we need to provide some default value
    if slug == "":
        slug = "-"

    ModelClass = instance.__class__

    search_field = f"{slug_field_name}__iregex"
    pattern = rf"{slug}-\d+$|{slug}$"
    lookup = {search_field: pattern}
    if additional_search_lookup:
        lookup.update(additional_search_lookup)

    slug_values = (
        ModelClass._default_manager.filter(**lookup)
        .exclude(pk=instance.pk)
        .values_list(slug_field_name, flat=True)
    )

    unique_slug = prepare_unique_slug(slug, slug_values)

    return unique_slug


def prepare_unique_slug(slug: str, slug_values: Iterable):
    """Prepare unique slug value based on provided list of existing slug values."""
    unique_slug: Union[SafeText, str] = slug
    extension = 1

    while unique_slug in slug_values:
        extension += 1
        unique_slug = f"{slug}-{extension}"

    return unique_slug


def prepare_unique_attribute_value_slug(attribute: "Attribute", slug: str):
    value_slugs = attribute.values.filter(slug__startswith=slug).values_list(
        "slug", flat=True
    )
    return prepare_unique_slug(slug, value_slugs)
