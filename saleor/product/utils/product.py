from typing import Iterable

from saleor.product.models import Product


def mark_products_for_recalculate_discounted_price(product_ids: Iterable[int]):
    """Mark products for recalculate discounted prices."""
    Product.objects.filter(pk__in=product_ids).update(discounted_price_dirty=True)
