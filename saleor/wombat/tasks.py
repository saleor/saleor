from order import Order
from requests import HTTPError
from rest_framework.renderers import JSONRenderer
from . import WombatClient, logger
from . import serializers

wombat = WombatClient()


def push_order(order):
    serialized_order = serializers.OrderSerializer(order)
    order_data = JSONRenderer().render(serialized_order.data)
    payload = {
        'orders': order_data
    }
    wombat_response = wombat.push(payload)
    try:
        wombat_response.raise_for_status()
    except HTTPError:
        logger.exception('Order push failed')
    else:
        logger.info('Order successfully pushed to Wombat')


def push_products(products_qs):
    products = serializers.ProductSerializer(products_qs, many=True)
    products_data = JSONRenderer().render(products.data)
    payload = {
        'products': products_data
    }
    wombat_response = wombat.push(payload)
    try:
        wombat_response.raise_for_status()
    except HTTPError:
        logger.exception('Products push failed')
    else:
        logger.info('Products successfully pushed to Wombat')
