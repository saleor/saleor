from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse

from ..base_plugin import BasePlugin


class MyPlugin(BasePlugin):
    """Test plugin into Saleor"""

    PLUGIN_NAME = "My Plugin"
    PLUGIN_ID = "my_plugin"
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
        return JsonResponse({"message": "Webhook - My plugin"})
