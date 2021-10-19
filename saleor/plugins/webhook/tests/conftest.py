import pytest

from ....plugins.manager import get_plugins_manager
from ....plugins.webhook.plugin import WebhookPlugin


@pytest.fixture
def webhook_plugin(settings):
    def factory() -> WebhookPlugin:
        settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
        manager = get_plugins_manager()
        return manager.global_plugins[0]

    return factory
