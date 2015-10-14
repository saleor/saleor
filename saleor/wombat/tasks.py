from order import Order
from requests import HTTPError
from rest_framework.renderers import JSONRenderer
from . import WombatClient, logger
from . import serializers

wombat = WombatClient()


def push_data(queryset):
    payload_config = serializers.PAYLOAD_CONFIG[queryset.model]
    serialized = payload_config['serializer_class'](queryset, many=True)
    json_data = JSONRenderer().render(serialized.data)
    wombat_response = wombat.push({
        payload_config['wombat_name']: json_data
    })
    try:
        wombat_response.raise_for_status()
    except HTTPError:
        logger.exception('Data push failed')
    else:
        logger.info('Data successfully pushed to Wombat')
