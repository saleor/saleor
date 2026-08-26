"""Entity-agnostic media helpers shared by the media and product GraphQL layers."""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import NamedTuple

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction

from ...core.exceptions import UnsupportedMediaProviderException
from ...core.http_client import HTTPClient
from ...core.utils.validators import (
    get_mime_type,
    get_oembed_data,
    is_image_mimetype,
    is_valid_image_content_type,
)
from ...product import MEDIA_URL_CHAR_LIMIT

logger = logging.getLogger(__name__)

ALT_CHAR_LIMIT = 250


class MediaValidationError(NamedTuple):
    message: str
    code: str
    field: str


def validate_media_input(
    image, media_url, alt, error_code_enum
) -> MediaValidationError | None:
    """Validate media input fields.

    Returns a MediaValidationError if validation fails, None otherwise.
    """
    if not image and not media_url:
        return MediaValidationError(
            message="Image or external URL is required.",
            code=error_code_enum.REQUIRED.value,
            field="",
        )
    if image and media_url:
        return MediaValidationError(
            message="Either image or external URL is required.",
            code=error_code_enum.DUPLICATED_INPUT_ITEM.value,
            field="",
        )
    if alt and len(alt) > ALT_CHAR_LIMIT:
        return MediaValidationError(
            message=f"Alt field exceeds the character limit of {ALT_CHAR_LIMIT}.",
            code=error_code_enum.INVALID.value,
            field="alt",
        )
    if media_url and len(media_url) > MEDIA_URL_CHAR_LIMIT:
        return MediaValidationError(
            message=f"URL field exceeds the character limit of {MEDIA_URL_CHAR_LIMIT}.",
            code=error_code_enum.INVALID.value,
            field="mediaUrl",
        )
    return None


@dataclass
class MediaUrlProbeResult:
    """Result of probing a media URL."""

    is_image: bool
    oembed_data: dict
    media_type: str


def probe_media_url(media_url: str, error_code_enum) -> MediaUrlProbeResult:
    """Probe a media URL to determine if it points to an image or oembed content.

    Returns a MediaUrlProbeResult indicating the type of media.
    Raises ValidationError if the URL points to an invalid image type
    or an unsupported media provider.
    """
    try:
        with HTTPClient.send_request(
            "GET",
            media_url,
            stream=True,
            allow_redirects=False,
            timeout=settings.COMMON_REQUESTS_TIMEOUT,
        ) as response:
            mime_type = get_mime_type(response.headers.get("content-type"))
    except requests.exceptions.RequestException as exc:
        raise ValidationError(
            {
                "media_url": ValidationError(
                    "Failed to fetch media from URL.",
                    code=error_code_enum.INVALID.value,
                )
            }
        ) from exc

    if is_image_mimetype(mime_type):
        if not is_valid_image_content_type(mime_type):
            raise ValidationError(
                {
                    "media_url": ValidationError(
                        "Invalid file type.",
                        code=error_code_enum.INVALID.value,
                    )
                }
            )
        return MediaUrlProbeResult(is_image=True, oembed_data={}, media_type="")

    try:
        oembed_data, media_type = get_oembed_data(media_url)
    except UnsupportedMediaProviderException as exc:
        raise ValidationError(
            {
                "media_url": ValidationError(
                    "Unsupported media provider or incorrect URL.",
                    code=error_code_enum.UNSUPPORTED_MEDIA_PROVIDER.value,
                )
            }
        ) from exc

    return MediaUrlProbeResult(
        is_image=False, oembed_data=oembed_data, media_type=media_type
    )


def update_ordered_media(ordered_media, error_code_enum):
    errors = defaultdict(list)
    with transaction.atomic():
        for order, media in enumerate(ordered_media):
            media.sort_order = order
            try:
                media.save(update_fields=["sort_order"])
            except DatabaseError as e:
                msg = (
                    f"Cannot update media for instance: {media}. "
                    "Updating not existing object. "
                    f"Details: {e}."
                )
                logger.warning(msg)
                errors["media"].append(
                    ValidationError(msg, code=error_code_enum.NOT_FOUND.value)
                )

    if errors:
        raise ValidationError(errors)


def sort_media(media, sort_by: dict | None):
    """Sort an already-loaded list of media in Python.

    Media is loaded through a dataloader as a whole gallery, so ordering it here
    avoids a second query per owner.
    """
    if sort_by is None:
        sort_by = {"field": ["sort_order"], "direction": ""}

    def key(media_obj):
        values = tuple(
            getattr(media_obj, field)
            for field in sort_by["field"]
            if getattr(media_obj, field) is not None
        )
        # Nullable values first, achieved by prefixing the number of non-null fields.
        return (len(values), *values)

    return sorted(media, key=key, reverse=sort_by["direction"] == "-")
