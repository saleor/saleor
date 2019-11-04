from typing import Optional

from django.db.models import Q, QuerySet
from django.utils.encoding import smart_text

from ...product.models import Product

IN_STOCK = "http://schema.org/InStock"
OUT_OF_STOCK = "http://schema.org/OutOfStock"


BRAND_SLUGS = ["brand", "publisher"]


def get_brand_from_attributes(attributes: QuerySet) -> Optional[str]:
    qs_filter_conditions = Q(assignment__attribute__slug__in=BRAND_SLUGS)
    qs = attributes.filter(qs_filter_conditions).prefetch_related("values")
    attribute = qs.first()
    if attribute is not None:
        return ", ".join([str(value) for value in attribute.values.all()])
    return None


def product_json_ld(product: Product):
    """Generate JSON-LD data for product."""
    data = {
        "@context": "http://schema.org/",
        "@type": "Product",
        "name": smart_text(product),
        "image": [product_image.image.url for product_image in product.images.all()],
        "description": product.plain_text_description,
        "offers": [],
    }

    for variant in product.variants.all():
        price = variant.get_price()
        in_stock = True
        if not product.is_visible or not variant.is_in_stock():
            in_stock = False
        variant_data = variant_json_ld(price, variant, in_stock)
        data["offers"].append(variant_data)

    brand = get_brand_from_attributes(product.attributes)
    if brand:
        data["brand"] = {"@type": "Thing", "name": brand}
    return data


def variant_json_ld(price, variant, in_stock):
    schema_data = {
        "@type": "Offer",
        "itemCondition": "http://schema.org/NewCondition",
        "priceCurrency": price.currency,
        "price": price.amount,
        "sku": variant.sku,
    }
    if in_stock:
        schema_data["availability"] = IN_STOCK
    else:
        schema_data["availability"] = OUT_OF_STOCK
    return schema_data
