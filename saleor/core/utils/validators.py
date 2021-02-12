import re
from typing import Tuple

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from ...product import ProductMediaTypes
from ...product.error_codes import ProductErrorCode


def validate_video_url(url: str, field_name: str) -> Tuple[str, str]:
    """Check the video URL and return the proper ProductMediaType."""
    youtube_pattern = re.compile(r"(?:youtube.com|youtu.be).*(?:v=|watch\/|\/)([\w]*)")
    streamable_pattern = re.compile(r"^(?:http[s]?://)?(?:www.)?streamable.com/([\w]*)")
    vimeo_pattern = re.compile(r"^(?:http[s]?://)?(?:www.)?vimeo.com/([\w]*)")

    is_youtube = re.search(youtube_pattern, url)
    is_streamable = re.search(streamable_pattern, url)
    is_vimeo = re.search(vimeo_pattern, url)

    if is_youtube:
        video_id = is_youtube.group(1)
        return (
            f"https://www.youtube.com/embed/{video_id}",
            ProductMediaTypes.VIDEO_YOUTUBE,
        )
    elif is_streamable:
        video_id = is_streamable.group(1)  # type: ignore
        return (
            f"https://www.streamable.com/e/{video_id}",
            ProductMediaTypes.VIDEO_STREAMABLE,
        )
    elif is_vimeo:
        video_id = is_vimeo.group(1)  # type: ignore
        return (
            f"https://player.vimeo.com/video/{video_id}",
            ProductMediaTypes.VIDEO_VIMEO,
        )

    try:
        url_validator = URLValidator()
        url_validator(url)
    except ValidationError:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Enter a valid URL.", code=ProductErrorCode.INVALID.value
                )
            }
        )

    return url, ProductMediaTypes.VIDEO_UNKNOWN
