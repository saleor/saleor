from unittest.mock import patch

import pytest

from ...manager import get_plugins_manager
from ..plugin import VatlayerPlugin


@pytest.fixture
def vatlayer_plugin(settings, vatlayer, channel_USD):
    def fun(
        active=True,
        access_key="key",
        origin_country=None,
        countries_to_calculate_taxes_from_origin=None,
        excluded_countries=None,
    ):
        settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
        manager = get_plugins_manager()
        with patch("saleor.plugins.vatlayer.plugin.fetch_rate_types"):
            manager.save_plugin_configuration(
                VatlayerPlugin.PLUGIN_ID,
                channel_USD.slug,
                {
                    "active": active,
                    "configuration": [
                        {"name": "Access key", "value": access_key},
                        {"name": "origin_country", "value": origin_country},
                        {
                            "name": "countries_to_calculate_taxes_from_origin",
                            "value": countries_to_calculate_taxes_from_origin,
                        },
                        {"name": "excluded_countries", "value": excluded_countries},
                    ],
                },
            )
        manager = get_plugins_manager()
        return manager.plugins_per_channel[channel_USD.slug][0]

    return fun
