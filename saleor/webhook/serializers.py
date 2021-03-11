from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..checkout.fetch import fetch_checkout_lines
from ..product.models import Product

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from ..checkout.models import Checkout
    from ..product.models import ProductVariant


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


def serialize_product_or_variant_attributes(
    product_or_variant: Union["Product", "ProductVariant"]
) -> List[Dict]:
    data = []
    for attr in product_or_variant.attributes.all():
        attr_data = {
            "name": attr.assignment.attribute.name,
            "id": attr.assignment.attribute.id,
            "values": [],
        }

        for attr_value in attr.values.all():
            value: Dict[str, Optional[Union[str, Dict[str, Any]]]] = {
                "name": attr_value.name,
                "slug": attr_value.slug,
                "file": None,
            }

            if attr_value.file_url:
                value["file"] = {
                    "content_type": attr_value.content_type,
                    "file_url": attr_value.file_url,
                }
            attr_data["values"].append(value)  # type: ignore

        data.append(attr_data)

    return data
