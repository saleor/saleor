import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.serializers.json import DjangoJSONEncoder

from ..core.utils import build_absolute_uri


def get_organization():
    site = Site.objects.get_current()
    organization_data = {
        '@type': 'Organization',
        'name': site.settings.brand_name}


def get_order_confirmation_schema(order):
    """Generates schema.org markup for order confirmation message."""
    organization = get_organization()
    order_url = build_absolute_uri(order.get_absolute_url())
    data = {
        '@context': 'http://schema.org',
        '@type': 'Order',
        'merchant': organization,
        'orderNumber': order.pk,
        'priceCurrency': order.total.currency,
        'price': order.total.gross,
        'acceptedOffer': [],
        'url': order_url,
        'potentialAction': {
            '@type': 'ViewAction',
            'url': order_url
        },
        'orderStatus': 'http://schema.org/OrderProcessing',
        'orderDate': order.created}

    for line in order.get_lines():
        product_data = {
            '@type': 'Offer',
            'itemOffered': {
                '@type': 'Product',
                'name': line.product_name,
                'sku': line.product_sku,
            },
            'price': line.unit_price_gross * line.quantity,
            'priceCurrency': order.total.currency,
            'eligibleQuantity': {
                '@type': 'QuantitativeValue',
                'value': line.quantity
            },
            'seller': organization}

        product = line.product
        if product:
            product_url = build_absolute_uri(product.get_absolute_url())
            product_data['itemOffered']['url'] = product_url

            image = product.get_first_image()
            if image:
                product_data['itemOffered']['image'] = build_absolute_uri(
                    location=image.url)
        data['acceptedOffer'].append(product_data)
    return json.dumps(data, cls=DjangoJSONEncoder)
