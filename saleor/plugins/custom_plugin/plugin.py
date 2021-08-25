import graphene
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse

from ..base_plugin import BasePlugin


class CustomPlugin(BasePlugin):
    """Test plugin into Saleor"""

    PLUGIN_NAME = "Custom Plugin"
    PLUGIN_ID = "custom_plugin"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = (
        "Test plugin into Saleor."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> JsonResponse:
        if path == '/webhook/test':
            # do something with the request
            return JsonResponse(data={"message": "Test plugin into Saleor"})
        return JsonResponse({"message": "Webhook - Custom plugin"})

    def detail_custom(self, info, custom_id, Custom):
        custom = graphene.Node.get_node_from_global_id(info, custom_id, Custom)
        return custom
