import pytest

from .sample_plugins import (
    ChannelPluginSample,
    InactiveChannelPluginSample,
    PluginInactive,
    PluginSample,
)


@pytest.mark.parametrize(
    "plugin_id, plugin_path, status_code",
    [
        (PluginSample.PLUGIN_ID, "/webhook/paid", 200),
        (PluginInactive.PLUGIN_ID, "/webhook/paid", 404),
        ("wrong.id", "/webhook/", 404),
    ],
)
def test_plugin_webhook_view(
    plugin_id, plugin_path, status_code, client, settings, monkeypatch
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    response = client.post(f"/plugins/{plugin_id}{plugin_path}")
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "plugin_id, plugin_path, status_code",
    [
        (PluginSample.PLUGIN_ID, "/webhook/paid", 200),
        (ChannelPluginSample.PLUGIN_ID, "/webhook/paid", 200),
        (InactiveChannelPluginSample.PLUGIN_ID, "/webhook/paid", 404),
        ("wrong.id", "/webhook/", 404),
    ],
)
def test_plugin_per_channel_webhook_view(
    plugin_id, plugin_path, status_code, client, settings, monkeypatch, channel_PLN
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.ChannelPluginSample",
        "saleor.plugins.tests.sample_plugins.InactiveChannelPluginSample",
    ]

    response = client.post(
        f"/plugins/channel/{channel_PLN.slug}/{plugin_id}{plugin_path}"
    )
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "plugin_id, plugin_path, status_code",
    [
        (PluginSample.PLUGIN_ID, "/webhook/paid", 200),
        (PluginInactive.PLUGIN_ID, "/webhook/paid", 404),
        ("wrong.id", "/webhook/", 404),
    ],
)
def test_plugin_global_webhook_view(
    plugin_id, plugin_path, status_code, client, settings, monkeypatch, channel_PLN
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
    ]

    response = client.post(f"/plugins/global/{plugin_id}{plugin_path}")
    assert response.status_code == status_code
