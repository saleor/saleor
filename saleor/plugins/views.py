from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse

from .manager import get_plugins_manager


def handle_plugin_webhook(request: WSGIRequest, plugin_id: str) -> HttpResponse:
    manager = get_plugins_manager()
    return manager.webhook(request, plugin_id)
