from unittest.mock import patch

import pytest

from ...manager import get_plugins_manager
from ..plugin import UserEmailPlugin


@pytest.fixture
def user_email_plugin(settings):
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

        settings.PLUGINS = ["saleor.plugins.user_email.plugin.UserEmailPlugin"]
        manager = get_plugins_manager()
        with patch(
            "saleor.plugins.user_email.plugin.validate_default_email_configuration"
        ):
            manager.save_plugin_configuration(
                UserEmailPlugin.PLUGIN_ID,
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
