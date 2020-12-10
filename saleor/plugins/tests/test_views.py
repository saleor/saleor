import pytest

from .sample_plugins import PluginInactive, PluginSample


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
