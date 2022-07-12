import logging
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.templatetags.static import static

from ..thumbnail.models import Thumbnail
from ..thumbnail.utils import get_image_or_proxy_url, get_thumbnail_size

if TYPE_CHECKING:
    from .models import ProductMedia


logger = logging.getLogger(__name__)


def get_product_image_thumbnail_url(product_media: Optional["ProductMedia"], size: int):
    """Return product media image thumbnail or placeholder if there is no image."""
    size = get_thumbnail_size(size)
    if not product_media or not product_media.image:
        return get_product_image_placeholder(size)
    thumbnail = Thumbnail.objects.filter(size=size, product_media=product_media).first()
    return get_image_or_proxy_url(
        thumbnail, product_media.id, "ProductMedia", size, None
    )


def get_product_image_placeholder(size: int):
    """Get a placeholder with the closest size to the provided value."""
    size = get_thumbnail_size(size)
    return static(settings.PLACEHOLDER_IMAGES[size])
