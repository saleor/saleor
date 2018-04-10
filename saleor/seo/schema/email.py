import json

from django.contrib.sites.models import Site
from django.core.serializers.json import DjangoJSONEncoder

from ...core.utils import build_absolute_uri


def get_organization():
    site = Site.objects.get_current()
    return {'@type': 'Organization', 'name': site.name}


def get_product_data(line, organization):
    gross_product_price = line.get_total().gross
    product_data = {
        '@type': 'Offer',
        'itemOffered': {
            '@type': 'Product',
            'name': line.product_name,
            'sku': line.product_sku,
        },
        'price': gross_product_price.amount,
        'priceCurrency': gross_product_price.currency,
        'eligibleQuantity': {
            '@type': 'QuantitativeValue',
            'value': line.quantity
        },
        'seller': organization}

    product = line.variant.product
    product_url = build_absolute_uri(product.get_absolute_url())
    product_data['itemOffered']['url'] = product_url

    image = product.get_first_image()
    if image:
        product_data['itemOffered']['image'] = build_absolute_uri(
            location=image.url)
    return product_data


def get_order_confirmation_markup(order):
    """Generates schema.org markup for order confirmation e-mail message."""
    organization = get_organization()
    order_url = build_absolute_uri(order.get_absolute_url())
    data = {
        '@context': 'http://schema.org',
        '@type': 'Order',
        'merchant': organization,
        'orderNumber': order.pk,
        'priceCurrency': order.total.gross.currency,
        'price': order.total.gross.amount,
        'acceptedOffer': [],
        'url': order_url,
        'potentialAction': {
            '@type': 'ViewAction',
            'url': order_url
        },
        'orderStatus': 'http://schema.org/OrderProcessing',
        'orderDate': order.created}

    lines = order.lines.prefetch_related('variant')
    for line in lines:
        product_data = get_product_data(line=line, organization=organization)
        data['acceptedOffer'].append(product_data)
    return json.dumps(data, cls=DjangoJSONEncoder)
