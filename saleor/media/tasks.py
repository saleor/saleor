import logging

from django.conf import settings

from ..celeryconf import app
from ..core.db.connection import allow_writer
from ..core.http_client import HTTPClient
from ..core.utils.url import sanitize_url_for_logging
from ..core.utils.validators import get_mime_type
from ..product import ProductMediaTypes
from ..product.utils.tasks_utils import (
    create_image,
    update_product_media,
    validate_content_type_header,
    validate_image_exif,
    validate_image_mime_type,
    validate_status_code,
)
from ..thumbnail.exceptions import ImageTooLargeError
from .utils import OWNER_TYPE_TO_MEDIA_MODEL

logger = logging.getLogger(__name__)


def delete_media_pending_image(owner_type: str, media_pk: int) -> None:
    """Drop a media row whose image could not be fetched.

    An image media with no file and no reachable external URL renders as a broken
    gallery entry, so the row goes rather than the gallery breaking.
    """
    OWNER_TYPE_TO_MEDIA_MODEL[owner_type].objects.filter(
        pk=media_pk, type=ProductMediaTypes.IMAGE
    ).delete()


def fetch_media_image(owner_type: str, media_pk: int) -> None:
    """Download the image at a media's external URL and store it on the row."""
    media_model = OWNER_TYPE_TO_MEDIA_MODEL[owner_type]
    media = media_model.objects.filter(
        pk=media_pk, type=ProductMediaTypes.IMAGE
    ).first()
    if media is None:
        logger.warning(
            "%s with id: %s with type: %s does not exist.",
            media_model.__name__,
            media_pk,
            ProductMediaTypes.IMAGE,
        )
        return

    if media.image:
        logger.error(
            "%s with id: %s already has an image.", media_model.__name__, media_pk
        )
        return

    if not media.external_url:
        logger.error(
            "%s with id: %s has neither an external URL nor an image. The object "
            "is in an invalid state and cannot be processed.",
            media_model.__name__,
            media_pk,
        )
        return

    with HTTPClient.send_request(
        "GET",
        media.external_url,
        stream=True,
        allow_redirects=False,
        timeout=settings.COMMON_REQUESTS_TIMEOUT,
    ) as response:
        validate_status_code(response.status_code)
        mime_type = get_mime_type(response.headers.get("content-type"))
        validate_content_type_header(media, mime_type)
        try:
            image = create_image(media, mime_type, response)
        except ValueError as error:
            logger.warning(
                "Image fetched for media %s was rejected: %s", media.pk, error
            )
            # NOTE: we do not wish to retry on this error hence why this exception
            #       isn't listed in `app.task(autoretry_for=...)` as this is a
            #       permanent error which will never be fixed upon retrying.
            raise

    validate_image_mime_type(image)
    try:
        validate_image_exif(image)
    except ImageTooLargeError as error:
        logger.warning(
            "Image fetched for media %s exceeds the pixel limit: %s",
            media.pk,
            sanitize_url_for_logging(media.external_url),
            extra={
                "image_source": sanitize_url_for_logging(media.external_url),
                "object_type": media_model.__name__,
                "object_pk": media.pk,
                "pillow_error": str(error),
            },
        )
        raise
    update_product_media(media, image)


def on_failure_fetch_media_image_task(self, exc, task_id, args, kwargs, einfo):
    owner_type, media_pk = args
    logger.warning(
        "Failed to fetch image for %s media with id: %s. Removing media.",
        owner_type,
        media_pk,
    )
    delete_media_pending_image(owner_type, media_pk)


@app.task(
    queue=settings.FETCH_IMAGES_QUEUE_NAME,
    max_retries=5,
    retry_backoff=True,
    default_retry_delay=1,
    autoretry_for=(IOError,),
    on_failure=on_failure_fetch_media_image_task,
    throws=(IOError, ValueError),
)
@allow_writer()
def fetch_media_image_task(owner_type: str, media_pk: int):
    fetch_media_image(owner_type, media_pk)
