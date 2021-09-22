import pytest

from saleor.payment.gateways.np_atobarai.plugin import (
    MERCHANT_CODE,
    SP_CODE,
    TERMINAL_ID,
    USE_SANDBOX,
    NPAtobaraiGatewayPlugin,
)

from .....plugins.manager import get_plugins_manager
from .....plugins.models import PluginConfiguration


@pytest.fixture
def np_atobarai_plugin(settings, monkeypatch, channel_USD):
    def fun(
        merchant_code="merchant-code",
        sp_code="sp-code",
        terminal_id="terminal-id",
        use_sandbox=True,
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
