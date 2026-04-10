import datetime
from typing import Any

import micawber

from ...product import ProductMediaTypes
from ..exceptions import UnsupportedMediaProviderException

SUPPORTED_MEDIA_TYPES = {
    "photo": ProductMediaTypes.IMAGE,
    "video": ProductMediaTypes.VIDEO,
}
MEDIA_MAX_WIDTH = 1920
MEDIA_MAX_HEIGHT = 1080


def get_oembed_data(url: str) -> tuple[dict[str, Any], str]:
    """Get the oembed data from URL or raise an ValidationError."""
    providers = micawber.bootstrap_basic()

    try:
        oembed_data = providers.request(
            url, maxwidth=MEDIA_MAX_WIDTH, maxheight=MEDIA_MAX_HEIGHT
        )
        return oembed_data, SUPPORTED_MEDIA_TYPES[oembed_data["type"]]
    except (micawber.exceptions.ProviderException, KeyError) as e:
        raise UnsupportedMediaProviderException() from e


def is_date_in_future(given_date):
    """Return true when the date is in the future."""
    return given_date > datetime.datetime.now(tz=datetime.UTC).date()


def get_mime_type(content_type_header: str | None) -> str | None:
    if content_type_header is None:
        return None
    return content_type_header.split(";", maxsplit=1)[0].strip().lower()


def is_image_mimetype(mimetype: str | None) -> bool:
    """Check if mimetype is image."""
    if mimetype is None:
        return False
    return mimetype.startswith("image/")


def is_valid_image_content_type(content_type: str | None) -> bool:
    """Check if content type is a valid image content type."""
    from ...thumbnail import MIME_TYPE_TO_PIL_IDENTIFIER

    return content_type is not None and content_type in MIME_TYPE_TO_PIL_IDENTIFIER
