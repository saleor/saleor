"""Entity-agnostic media domain logic.

Media rows live on one table but are exposed as one GraphQL type per owner, and
their global IDs are owner-typed. The lookup tables below are the single source of
truth for that correspondence; they live in the domain layer because the webhook
payload and dispatch paths need them as much as the GraphQL layer does. The same
goes for media validation, remote-URL probing and gallery ordering: the GraphQL
mutations only orchestrate them.
"""

from dataclasses import dataclass
from typing import NamedTuple

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from ..core.exceptions import UnsupportedMediaProviderException
from ..core.http_client import HTTPClient
from ..core.utils.validators import (
    get_mime_type,
    get_oembed_data,
    is_image_mimetype,
    is_valid_image_content_type,
)
from ..page import models as page_models
from ..permission.enums import BasePermissionEnum, PagePermissions, ProductPermissions
from . import MEDIA_URL_CHAR_LIMIT, MediaOwnerTypes, ProductMediaTypes
from . import models as product_models
from .lock_objects import product_media_qs_select_for_update

ALT_CHAR_LIMIT = 250

OWNER_TYPE_TO_MODEL: dict[str, type] = {
    MediaOwnerTypes.PRODUCT: product_models.Product,
    MediaOwnerTypes.CATEGORY: product_models.Category,
    MediaOwnerTypes.COLLECTION: product_models.Collection,
    MediaOwnerTypes.PAGE: page_models.Page,
}

# GraphQL enum member name (`PRODUCT`) -> stored owner type (`product`).
ENUM_NAME_TO_OWNER_TYPE: dict[str, str] = {
    owner_type.upper(): owner_type for owner_type in MediaOwnerTypes.ALL
}

OWNER_TYPE_TO_GRAPHQL_TYPE: dict[str, str] = {
    MediaOwnerTypes.PRODUCT: "Product",
    MediaOwnerTypes.CATEGORY: "Category",
    MediaOwnerTypes.COLLECTION: "Collection",
    MediaOwnerTypes.PAGE: "Page",
}
GRAPHQL_TYPE_TO_OWNER_TYPE = {
    graphql_type: owner_type
    for owner_type, graphql_type in OWNER_TYPE_TO_GRAPHQL_TYPE.items()
}

OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE: dict[str, str] = {
    MediaOwnerTypes.PRODUCT: "ProductMedia",
    MediaOwnerTypes.CATEGORY: "CategoryMedia",
    MediaOwnerTypes.COLLECTION: "CollectionMedia",
    MediaOwnerTypes.PAGE: "PageMedia",
}
MEDIA_GRAPHQL_TYPE_TO_OWNER_TYPE = {
    media_type: owner_type
    for owner_type, media_type in OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE.items()
}

MEDIA_OWNER_PERMISSION_MAP: dict[str, BasePermissionEnum] = {
    MediaOwnerTypes.PRODUCT: ProductPermissions.MANAGE_PRODUCTS,
    MediaOwnerTypes.CATEGORY: ProductPermissions.MANAGE_PRODUCTS,
    MediaOwnerTypes.COLLECTION: ProductPermissions.MANAGE_PRODUCTS,
    MediaOwnerTypes.PAGE: PagePermissions.MANAGE_PAGES,
}

# Owner event fired alongside every media change, for storefront cache busting.
OWNER_TYPE_TO_UPDATED_EVENT: dict[str, str] = {
    MediaOwnerTypes.PRODUCT: "product_updated",
    MediaOwnerTypes.CATEGORY: "category_updated",
    MediaOwnerTypes.COLLECTION: "collection_updated",
    MediaOwnerTypes.PAGE: "page_updated",
}


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


def create_media_from_url(
    owner, media_url: str, alt: str, probe_result: MediaUrlProbeResult
) -> product_models.ProductMedia:
    """Attach a media row for an already-probed remote URL to `owner`.

    An image URL is only recorded here; the file itself is downloaded by
    `fetch_product_media_image_task`, which the caller schedules after commit.
    """
    if probe_result.is_image:
        return owner.media.create(
            external_url=media_url, alt=alt, type=ProductMediaTypes.IMAGE
        )
    oembed_data = probe_result.oembed_data
    return owner.media.create(
        external_url=oembed_data["url"],
        alt=oembed_data.get("title", alt),
        type=probe_result.media_type,
        oembed_data=oembed_data,
    )


def update_media_order(
    ordered_media: list[product_models.ProductMedia], error_code_enum
) -> None:
    """Renumber `sort_order` to match the given order, in a single write.

    The rows are locked first so two concurrent reorders of the same gallery
    serialize instead of interleaving into an order neither request asked for.
    Locking also settles whether every row still exists: one deleted concurrently
    aborts the whole reorder rather than leaving a partially renumbered gallery.
    """
    with transaction.atomic():
        locked_pks = set(
            product_media_qs_select_for_update()
            .filter(pk__in=[media.pk for media in ordered_media])
            .values_list("pk", flat=True)
        )
        missing_pks = [
            media.pk for media in ordered_media if media.pk not in locked_pks
        ]
        if missing_pks:
            raise ValidationError(
                {
                    "media": ValidationError(
                        f"Cannot update media that no longer exists: {missing_pks}.",
                        code=error_code_enum.NOT_FOUND.value,
                    )
                }
            )
        for order, media in enumerate(ordered_media):
            media.sort_order = order
        product_models.ProductMedia.objects.bulk_update(ordered_media, ["sort_order"])
