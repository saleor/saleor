import json
from typing import TYPE_CHECKING

from django.contrib.sites.models import Site

from ...core.utils import build_absolute_uri
from ...core.utils.json_serializer import HTMLSafeJSON

if TYPE_CHECKING:
    from ...order.models import Order, OrderLine


def get_organization():
    site = Site.objects.get_current()
    return {"@type": "Organization", "name": site.name}


def get_product_data(line: "OrderLine", organization: dict) -> dict:
    gross_product_price = line.total_price.gross
    line_name = str(line)
    if line.translated_product_name:
        line_name = (
            f"{line.translated_product_name} ({line.translated_variant_name})"
            if line.translated_variant_name
            else line.translated_product_name
        )
    product_data = {
        "@type": "Offer",
        "itemOffered": {
            "@type": "Product",
            "name": line_name,
            "sku": line.product_sku or line.product_variant_id,
        },
        "price": gross_product_price.amount,
        "priceCurrency": gross_product_price.currency,
        "eligibleQuantity": {"@type": "QuantitativeValue", "value": line.quantity},
        "seller": organization,
    }

    if not line.variant:
        return {}

    product = line.variant.product
    product_image = product.get_first_image()
    if product_image:
        image = product_image.image
        product_data["itemOffered"]["image"] = build_absolute_uri(location=image.url)
    return product_data


def get_order_confirmation_markup(order: "Order") -> str:
    """Generate schema.org markup for order confirmation e-mail message."""
    organization = get_organization()
    data = {
        "@context": "http://schema.org",
        "@type": "Order",
        "merchant": organization,
        "orderNumber": order.pk,
        "priceCurrency": order.total.gross.currency,
        "price": order.total.gross.amount,
        "acceptedOffer": [],
        "orderStatus": "http://schema.org/OrderProcessing",
        "orderDate": order.created_at,
    }

    for line in order.lines.all():
        product_data = get_product_data(line=line, organization=organization)
        data["acceptedOffer"].append(product_data)
    return json.dumps(data, cls=HTMLSafeJSON)
