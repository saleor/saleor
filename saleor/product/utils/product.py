from collections.abc import Iterable
from typing import Optional

from ...product.models import ProductChannelListing


def mark_products_for_recalculate_discounted_price(
    product_ids: Iterable[int], channel_ids: Optional[Iterable[int]] = None
):
    """Mark products for recalculate discounted prices."""
    if channel_ids is None:
        ProductChannelListing.objects.filter(product_id__in=product_ids).update(
            discounted_price_dirty=True
        )
    else:
        ProductChannelListing.objects.filter(
            product_id__in=product_ids, channel_id__in=channel_ids
        ).update(discounted_price_dirty=True)
