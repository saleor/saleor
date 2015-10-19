from requests import HTTPError
from rest_framework.renderers import JSONRenderer
from . import WombatClient, logger
from . import serializers

wombat = WombatClient()


def push_data(queryset, serializer_class, wombat_name):
    serialized = serializer_class(queryset, many=True)
    json_data = JSONRenderer().render(serialized.data)
    wombat_response = wombat.push({wombat_name: json_data})
    try:
        wombat_response.raise_for_status()
    except HTTPError:
        logger.exception('Data push failed')
    else:
        logger.info('Data successfully pushed to Wombat')


def push_products(queryset):
    return push_data(queryset, serializers.ProductSerializer, 'products')


def push_orders(queryset):
    return push_data(queryset, serializers.OrderSerializer, 'orders')
