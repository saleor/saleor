from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from ..checkout.models import Checkout


def serialize_checkout_lines(checkout: "Checkout") -> List[dict]:
    data = []
    channel = checkout.channel
    for line in checkout.lines.select_related("variant__product").all():
        variant = line.variant
        channel_listing = variant.channel_listings.get(channel=channel)
        product = variant.product
        # TODO: optimize getting arguments for get_price
        base_price = variant.get_price(product, [], channel, channel_listing)
        data.append(
            {
                "sku": variant.sku,
                "quantity": line.quantity,
                "base_price": str(base_price.amount),
                "currency": channel.currency_code,
                "full_name": variant.display_product(),
                "product_name": product.name,
                "variant_name": variant.name,
            }
        )
    return data
