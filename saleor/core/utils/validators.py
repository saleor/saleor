from typing import Any, Dict, Tuple

import micawber
from django.core.exceptions import ValidationError

from ...product import ProductMediaTypes
from ...product.error_codes import ProductErrorCode

SUPPORTED_MEDIA_TYPES = {
    "photo": ProductMediaTypes.IMAGE,
    "video": ProductMediaTypes.VIDEO,
}


def get_oembed_data(url: str, field_name: str) -> Tuple[Dict[str, Any], str]:
    """Get the oembed data from URL or raise an ValidationError."""
    providers = micawber.bootstrap_basic()

    try:
        oembed_data = providers.request(url, maxwidth=800, maxheight=600)
        return oembed_data, SUPPORTED_MEDIA_TYPES[oembed_data["type"]]
    except micawber.exceptions.ProviderException:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Incorrect URL or unsupported media provider.",
                    code=ProductErrorCode.INVALID.value,
                )
            }
        )
    except KeyError:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Unsupported media type.", code=ProductErrorCode.INVALID.value
                )
            }
        )
