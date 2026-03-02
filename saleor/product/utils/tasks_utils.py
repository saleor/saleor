from typing import IO

from PIL import Image, UnidentifiedImageError
from requests.exceptions import HTTPError

from ...core.utils import create_file_from_response
from ...core.utils.validators import is_valid_image_content_type
from ...thumbnail.utils import ProcessedImage, get_filename_from_url


def validate_status_code(status_code):
    if status_code >= 500:
        raise HTTPError(f"Retryable error (HTTP status: {status_code}).")

    if status_code < 200 or status_code >= 300:
        raise ValueError(f"Non-retryable error (HTTP status: {status_code}).")


def validate_content_type_header(product_media, mime_type):
    if not is_valid_image_content_type(mime_type):
        raise ValueError(
            f"File from product media: {product_media.pk} does not have "
            f"valid image content-type: {mime_type}."
        )


def create_image(product_media, mime_type, response):
    filename = get_filename_from_url(product_media.external_url, mime_type)
    return create_file_from_response(response, filename)


def validate_image_mime_type(image: IO[bytes]):
    try:
        # Validate by reading MIME type from magic bytes.
        ProcessedImage.get_image_metadata_from_file(image)
    finally:
        image.seek(0)


def validate_image_exif(image: IO[bytes]):
    try:
        # Validate by getting exif.
        pil_image_obj = Image.open(image)
        pil_image_obj.getexif()
    except (
        ValueError,
        TypeError,
        SyntaxError,
        UnidentifiedImageError,
    ) as exc:
        raise ValueError(exc) from exc
    finally:
        image.seek(0)


def update_product_media(product_media, image):
    product_media.image = image
    product_media.external_url = None
    product_media.save(update_fields=["image", "external_url"])
