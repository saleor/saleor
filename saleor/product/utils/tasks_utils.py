from typing import IO

from django.db.utils import OperationalError
from PIL import Image, UnidentifiedImageError

from ...core.utils import create_file_from_response
from ...core.utils.validators import is_image_mimetype, is_valid_image_content_type
from ...product import ProductMediaTypes
from ...thumbnail.utils import ProcessedImage, get_filename_from_url
from ..models import ProductMedia


class RetryableError(Exception):
    pass


class NonRetryableError(Exception):
    def __init__(self, msg, reraise=False) -> None:
        super().__init__(msg)
        self.reraise = reraise


class UnhandledException(Exception):
    """The point of this exception is to not get handled.

    This will be thrown in cases where crash is intentional, in order to indicate a
    greater problem that has occurred.
    """


def get_product_media(product_media_id: int):
    try:
        return ProductMedia.objects.get(
            pk=product_media_id, type=ProductMediaTypes.IMAGE
        )
    except ProductMedia.DoesNotExist as exc:
        raise NonRetryableError(
            f"Cannot find product media of type: {ProductMediaTypes.IMAGE} with id: {product_media_id}."
        ) from exc


def validate_product_media_image(product_media: ProductMedia):
    if product_media.image:
        raise NonRetryableError(
            f"Product media with id: {product_media.pk} already has an image."
        )


def validate_product_media_external_url(product_media: ProductMedia):
    if not product_media.external_url:
        raise UnhandledException(
            f"Product media with id: {product_media.pk} has neither an external "
            f"URL nor an image. The object is in an invalid state and cannot be "
            f"processed.",
        )


def validate_status_code(status_code):
    if status_code >= 500:
        raise RetryableError(f"Server error (HTTP status: {status_code}).")

    if status_code < 200 or status_code >= 300:
        raise NonRetryableError(
            f"Informational or client error happened (HTTP status: {status_code})"
        )


def validate_content_type_header(product_media, mime_type):
    if not is_image_mimetype(mime_type) or not is_valid_image_content_type(mime_type):
        raise NonRetryableError(
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
    except ValueError as exc:
        raise NonRetryableError(exc) from exc
    finally:
        image.seek(0)


def validate_image_exif(image: IO[bytes]):
    try:
        # Validate with by getting exif.
        pil_image_obj = Image.open(image)
        pil_image_obj.getexif()
    except (
        ValueError,
        TypeError,
        SyntaxError,
        UnidentifiedImageError,
    ) as exc:
        raise NonRetryableError(exc) from exc
    finally:
        image.seek(0)


def update_product_media(product_media, image):
    try:
        product_media.image = image
        product_media.external_url = None
        product_media.save(update_fields=["image", "external_url"])
    except OperationalError as exc:
        raise RetryableError(exc) from exc
