import re
from typing import Tuple

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from ...product import ProductMediaTypes
from ...product.error_codes import ProductErrorCode


def validate_video_url(url: str, field_name: str) -> Tuple[str, str]:
    """Check the video URL and return the proper ProductMediaType."""
    youtube_pattern = re.compile(r"(?:youtube.com|youtu.be).*(?:v=|watch\/|\/)([\w]*)")
    is_youtube = re.search(youtube_pattern, url)

    if is_youtube:
        video_id = is_youtube.group(1)
        return (
            f"https://www.youtube.com/embed/{video_id}",
            ProductMediaTypes.VIDEO_YOUTUBE,
        )
    elif "streamable.com" in url:
        pattern = re.compile(r"streamable\.com/([\w]*)")
        match = re.search(pattern, url)
        video_id = match.group(1)  # type: ignore
        return (
            f"https://www.streamable.com/e/{video_id}",
            ProductMediaTypes.VIDEO_STREAMABLE,
        )
    elif "vimeo.com" in url:
        pattern = re.compile(r"vimeo\.com/([\w]*)")
        match = re.search(pattern, url)
        video_id = match.group(1)  # type: ignore
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
