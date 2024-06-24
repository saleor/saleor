from collections.abc import Collection
from typing import Optional

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

from . import (
    ICON_MIME_TYPES,
    MIME_TYPE_TO_PIL_IDENTIFIER,
    MIN_ICON_SIZE,
    PIL_IDENTIFIER_TO_MIME_TYPE,
)


def validate_image_format(
    img: Image.Image,
    error_code: str,
    allowed_mimetypes: Collection[str] = MIME_TYPE_TO_PIL_IDENTIFIER,
):
    image_mimetype = PIL_IDENTIFIER_TO_MIME_TYPE.get(img.format) if img.format else None
    if not image_mimetype or image_mimetype not in allowed_mimetypes:
        msg = f"Invalid file format. Only: {', '.join(allowed_mimetypes)} are supported"
        raise ValidationError(msg, code=error_code)


def validate_image_exif(img: Image.Image, error_code: str):
    try:
        img.getexif()
    except (SyntaxError, TypeError, UnidentifiedImageError) as e:
        raise ValidationError(
            "Invalid file. The following error was raised during the attempt "
            f"of getting the exchangeable image file data: {str(e)}.",
            code=error_code,
        )


def validate_image_size(
    img: Image.Image,
    error_code: str,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    square_required=False,
):
    if min_size and img.size < (min_size, min_size):
        msg = f"Invalid file. Minimal accepted image size is {min_size}x{min_size}."
        raise ValidationError(msg, code=error_code)
    if max_size and img.size > (max_size, max_size):
        msg = f"Invalid file. Maximal accepted image size is {max_size}x{max_size}."
        raise ValidationError(msg, code=error_code)
    if square_required and img.size[0] != img.size[1]:
        msg = "Invalid file. Image must be square"
        raise ValidationError(msg, code=error_code)


def validate_icon_image(image_file, error_code: str):
    file_pos = image_file.tell()
    try:
        with Image.open(image_file) as image:
            validate_image_format(image, error_code, ICON_MIME_TYPES)
            validate_image_size(image, error_code, MIN_ICON_SIZE, square_required=True)
    except (
        SyntaxError,
        TypeError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ) as e:
        raise ValidationError(
            "Invalid file. The following error was raised during the attempt "
            f"of opening the file: {str(e)}",
            code=error_code,
        )
    finally:
        image_file.seek(file_pos)
