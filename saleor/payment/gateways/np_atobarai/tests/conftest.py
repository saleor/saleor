import pytest

from .....plugins.manager import get_plugins_manager
from .....plugins.models import PluginConfiguration
from ..const import (
    FILL_MISSING_ADDRESS,
    MERCHANT_CODE,
    SP_CODE,
    TERMINAL_ID,
    USE_SANDBOX,
)
from ..plugin import NPAtobaraiGatewayPlugin


@pytest.fixture
def np_atobarai_plugin(settings, monkeypatch, channel_USD):
    def fun(
        merchant_code="merchant-code",
        sp_code="sp-code",
        terminal_id="terminal-id",
        use_sandbox=True,
        fill_missing_address=True,
        active=True,
    ):
        settings.PLUGINS = [
            "saleor.payment.gateways.np_atobarai.plugin.NPAtobaraiGatewayPlugin"
        ]

        configuration = [
            {"name": MERCHANT_CODE, "value": merchant_code},
            {"name": SP_CODE, "value": sp_code},
            {"name": TERMINAL_ID, "value": terminal_id},
            {"name": USE_SANDBOX, "value": use_sandbox},
            {"name": FILL_MISSING_ADDRESS, "value": fill_missing_address},
        ]
        PluginConfiguration.objects.create(
            identifier=NPAtobaraiGatewayPlugin.PLUGIN_ID,
            name=NPAtobaraiGatewayPlugin.PLUGIN_NAME,
            description="",
            active=active,
            channel=channel_USD,
            configuration=configuration,
        )

        manager = get_plugins_manager()
        return manager.plugins_per_channel[channel_USD.slug][0]

    return fun
