from datetime import date
from typing import Any, Dict, Optional, Tuple

import micawber
from django.core.exceptions import ValidationError

from ...account.models import User
from ...product import ProductMediaTypes
from ...product.error_codes import ProductErrorCode

SUPPORTED_MEDIA_TYPES = {
    "photo": ProductMediaTypes.IMAGE,
    "video": ProductMediaTypes.VIDEO,
}
MEDIA_MAX_WIDTH = 1920
MEDIA_MAX_HEIGHT = 1080


def get_oembed_data(url: str, field_name: str) -> Tuple[Dict[str, Any], str]:
    """Get the oembed data from URL or raise an ValidationError."""
    providers = micawber.bootstrap_basic()

    try:
        oembed_data = providers.request(
            url, maxwidth=MEDIA_MAX_WIDTH, maxheight=MEDIA_MAX_HEIGHT
        )
        return oembed_data, SUPPORTED_MEDIA_TYPES[oembed_data["type"]]
    except (micawber.exceptions.ProviderException, KeyError):
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Unsupported media provider or incorrect URL.",
                    code=ProductErrorCode.UNSUPPORTED_MEDIA_PROVIDER.value,
                )
            }
        )


def user_is_valid(user: Optional[User]) -> bool:
    """Return True when user is provided and is not anonymous."""
    return bool(user and not user.is_anonymous)


def is_date_in_future(given_date):
    """Return true when the date is in the future."""
    return given_date > date.today()
