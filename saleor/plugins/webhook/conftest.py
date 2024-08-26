import pytest

from ..manager import get_plugins_manager


@pytest.fixture
def webhook_plugin(settings):
    def factory():
        settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
        manager = get_plugins_manager(allow_replica=False)
        manager.get_all_plugins()
        return manager.global_plugins[0]

    return factory
