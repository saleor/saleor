from django.http import HttpResponse

from ..core.db.connection import allow_writer
from ..graphql.core import SaleorContext
from .manager import get_plugins_manager


@allow_writer()
def handle_plugin_webhook(request: SaleorContext, plugin_id: str) -> HttpResponse:
    manager = get_plugins_manager(allow_replica=False)
    return manager.webhook_endpoint_without_channel(request, plugin_id)


@allow_writer()
def handle_global_plugin_webhook(
    request: SaleorContext, plugin_id: str
) -> HttpResponse:
    manager = get_plugins_manager(allow_replica=False)
    return manager.webhook(request, plugin_id, channel_slug=None)


@allow_writer()
def handle_plugin_per_channel_webhook(
    request: SaleorContext, plugin_id: str, channel_slug: str
) -> HttpResponse:
    manager = get_plugins_manager(allow_replica=False)
    return manager.webhook(request, plugin_id, channel_slug=channel_slug)
