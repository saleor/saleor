"""Pack allocation utilities for product packs in checkout."""

from typing import TYPE_CHECKING

from ..core.utils.apportionment import hamilton

if TYPE_CHECKING:
    from ..channel.models import Channel
    from ..product.models import Product, ProductVariant


def get_pack_for_product(
    product: "Product",
    pack_size: int,
    channel: "Channel",
    warehouse_ids: list[str] | None = None,
) -> list[tuple["ProductVariant", int]]:
    """Select variants for pack using Hamilton's method for fair allocation.

    Take the total available quantity and fairly allocate at most pack_size
    variants. If stock runs out only allocate what is available.

    eg. 5 smalls, 10 mediums, 40 larges (pack_size=10)
    -> [(small, 1), (medium, 2), (large, 7)]

    Uses Hamilton's method for proportional allocation:
    https://en.wikipedia.org/wiki/Mathematics_of_apportionment

    allocation[variant] = pack_size x (variant_stock / total_stock)
    """
    from ..warehouse.availability import get_available_quantity

    variants = list(product.variants.all())
    if not variants:
        return []

    country_code = channel.default_country.code
    variant_stock = {}
    total_stock = 0

    for variant in variants:
        available = get_available_quantity(
            variant,
            country_code,
            channel.slug,
            check_reservations=True,
            warehouse_ids=warehouse_ids,
        )
        if available > 0:
            variant_stock[variant] = available
            total_stock += available

    if total_stock == 0:
        return []

    actual_pack_size = min(pack_size, total_stock)
    allocations = hamilton(variant_stock, actual_pack_size)
    return [(variant, qty) for variant, qty in allocations.items() if qty > 0]
