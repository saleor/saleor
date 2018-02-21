import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.serializers.json import DjangoJSONEncoder

from ..core.utils import build_absolute_uri


def get_organization():
    site = Site.objects.get_current()
    return {
        '@type': 'Organization',
        'name': site.settings.name}


def get_product_data(line, currency, organization):
    product_data = {
        '@type': 'Offer',
        'itemOffered': {
            '@type': 'Product',
            'name': line.product_name,
            'sku': line.product_sku,
        },
        'price': line.unit_price_gross * line.quantity,
        'priceCurrency': currency,
        'eligibleQuantity': {
            '@type': 'QuantitativeValue',
            'value': line.quantity
        },
        'seller': organization}

    product = line.product
    product_url = build_absolute_uri(product.get_absolute_url())
    product_data['itemOffered']['url'] = product_url

    image = product.get_first_image()
    if image:
        product_data['itemOffered']['image'] = build_absolute_uri(
            location=image.url)
    return product_data


def get_order_confirmation_schema(order):
    """Generates schema.org markup for order confirmation e-mail message."""
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
        product_data = get_product_data(
            line=line, currency=order.total.currency,
            organization=organization)
        data['acceptedOffer'].append(product_data)
    return json.dumps(data, cls=DjangoJSONEncoder)
