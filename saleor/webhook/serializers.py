from typing import TYPE_CHECKING, List

from ..checkout.utils import fetch_checkout_lines

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from ..checkout.models import Checkout


def serialize_checkout_lines(checkout: "Checkout") -> List[dict]:
    data = []
    channel = checkout.channel
    for line_info in fetch_checkout_lines(checkout):
        variant = line_info.variant
        channel_listing = line_info.channel_listing
        collections = line_info.collections
        product = variant.product
        base_price = variant.get_price(product, collections, channel, channel_listing)
        data.append(
            {
                "sku": variant.sku,
                "quantity": line_info.line.quantity,
                "base_price": str(base_price.amount),
                "currency": channel.currency_code,
                "full_name": variant.display_product(),
                "product_name": product.name,
                "variant_name": variant.name,
            }
        )
    return data
