from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http.request import split_domain_port, validate_host


def validate_storefront_url(url):
    """Validate the storefront URL.

    Raise ValidationError if URL isn't in RFC 1808 format
    or it isn't allowed by ALLOWED_STOREFRONT_HOSTS in settings.
    """
    try:
        parsed_url = urlparse(url)
        domain, _ = split_domain_port(parsed_url.netloc)
    except ValueError as error:
        raise ValidationError({"redirectUrl": str(error)})
    if not validate_host(domain, settings.ALLOWED_STOREFRONT_HOSTS):
        raise ValidationError({"redirectUrl": f"{domain} this is not allowed address."})
