import pytest

from ...manager import get_plugins_manager
from ..plugin import UserEmailPlugin


@pytest.fixture
def user_email_plugin(settings):
    def fun():
        settings.PLUGINS += ["saleor.plugins.user_email.plugin.UserEmailPlugin"]
        manager = get_plugins_manager()
        manager.save_plugin_configuration(
            UserEmailPlugin.PLUGIN_ID, {"active": True, "configuration": []}
        )
        manager = get_plugins_manager()
        return manager.plugins[0]

    return fun
