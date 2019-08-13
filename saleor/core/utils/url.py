from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http.request import validate_host


def validate_storefront_url(url):
    """Validate the storefront URL.

    Raise ValidationError if URL isn't in RFC 1808 format
    or it isn't allowed by ALLOWED_STOREFRONT_HOSTS in settings.
    """
    try:
        parsed_url = urlparse(url)
    except ValueError as error:
        raise ValidationError({"redirectUrl": str(error)})
    if not validate_host(parsed_url.netloc, settings.ALLOWED_STOREFRONT_HOSTS):
        raise ValidationError(
            {
                "redirectUrl": "%s this is not valid storefront address."
                % parsed_url.netloc
            }
        )
