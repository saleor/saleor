from urllib.parse import urlparse, urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.http.request import split_domain_port, validate_host

from . import build_absolute_uri


def validate_storefront_url(url):
    """Validate the storefront URL.

    Raise ValidationError if URL isn't in RFC 1808 format
    or it isn't allowed by ALLOWED_CLIENT_HOSTS in settings.
    """
    try:
        parsed_url = urlparse(url)
        domain, _ = split_domain_port(parsed_url.netloc)
        if not parsed_url.netloc:
            raise ValidationError(
                "Invalid URL. Please check if URL is in RFC 1808 format."
            )
    except ValueError as error:
        raise ValidationError(str(error))
    if not validate_host(domain, settings.ALLOWED_CLIENT_HOSTS):
        error_message = (
            f"{domain or url} is not allowed. Please check "
            "`ALLOWED_CLIENT_HOSTS` configuration."
        )
        raise ValidationError(error_message)


def prepare_url(params: str, redirect_url: str) -> str:
    """Add params to redirect url."""
    split_url = urlsplit(redirect_url)
    current_params = split_url.query
    if current_params:
        params = f"{current_params}&{params}"
    split_url = split_url._replace(query=params)
    return split_url.geturl()


def get_default_storage_root_url():
    """Return the absolute root URL for default storage."""
    # We cannot do simple `storage.url("")`, as the `AzureStorage` url method requires
    # at least one printable character that is not a slash or space.
    # Because of that, the `url` method is called for a `path` value, and then
    # `path` is stripped to get the actual root URL
    tmp_path = "path"
    return build_absolute_uri(default_storage.url(tmp_path)).rstrip(tmp_path)
