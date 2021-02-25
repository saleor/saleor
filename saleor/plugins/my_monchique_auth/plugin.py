from typing import Any
from uuid import uuid4

from ..base_plugin import BasePlugin
from ...monchique.network import create_user, custom_login

class MyMonchiqueAuthPlugin(BasePlugin):
    PLUGIN_ID = "quleap.auth.mymonchique"
    PLUGIN_NAME = "MyMonchiqueAuth"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Built-in saleor plugin that handles invoice creation."

    def custom_auth(self, payload, previous_value: Any) -> Any:
        return custom_login(payload['email'], payload['password'])

    def register_account(self, payload, previous_value: Any) -> bool:
        return create_user(payload["name"], payload["email"], payload["username"], payload["password"])
