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
