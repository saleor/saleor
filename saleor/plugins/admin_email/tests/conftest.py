import pytest

from ...manager import get_plugins_manager
from ..plugin import AdminEmailPlugin


@pytest.fixture
def admin_email_plugin(settings):
    def fun(
        host="localhost",
        port="1025",
        username=None,
        password=None,
        sender_name="Admin Name",
        sender_address="admin@example.com",
        use_tls=False,
        use_ssl=False,
        active=True,
    ):
        settings.PLUGINS = ["saleor.plugins.admin_email.plugin.AdminEmailPlugin"]
        manager = get_plugins_manager()
        manager.save_plugin_configuration(
            AdminEmailPlugin.PLUGIN_ID,
            {
                "active": active,
                "configuration": [
                    {"name": "host", "value": host},
                    {"name": "port", "value": port},
                    {"name": "username", "value": username},
                    {"name": "password", "value": password},
                    {"name": "sender_name", "value": sender_name},
                    {"name": "sender_address", "value": sender_address},
                    {"name": "use_tls", "value": use_tls},
                    {"name": "use_ssl", "value": use_ssl},
                ],
            },
        )
        manager = get_plugins_manager()
        return manager.plugins[0]

    return fun
