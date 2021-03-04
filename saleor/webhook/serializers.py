from collections import defaultdict
from typing import TYPE_CHECKING, List, Union
from django.db.models import F

from ..attribute.models import AssignedVariantAttribute, AssignedProductAttribute
from ..product.models import Product
from ..checkout.fetch import fetch_checkout_lines

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


def serialize_product_attributes(
    product: Union["Product", "ProductVariant"]
) -> List[dict]:
    queryset = (
        (
            AssignedProductAttribute.objects.filter(product_id=product.id)
            if isinstance(product, Product)
            else AssignedVariantAttribute.objects.filter(variant_id=product.id)
        )
        .values(
            attribute_name=F("assignment__attribute__name"),
            attribute_id=F("assignment__attribute__id"),
            name=F("values__name"),
            value=F("values__value"),
            slug=F("values__slug"),
        )
        .order_by("assignment__attribute__id")
    )

    values = defaultdict(list)
    for row in queryset:
        values[row["attribute_id"]].append(
            {"name": row["name"], "value": row["value"], "slug": row["slug"]}
        )

    return [
        {
            "name": row["attribute_name"],
            "id": row["attribute_id"],
            "values": values[row["attribute_id"]],
        }
        for row in queryset.distinct("assignment__attribute__id")
    ]
