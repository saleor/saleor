from saleor.plugins.urls import register_plugins_urls


def test_register_plugins_urls(settings):
    settings.PLUGINS = ["tests.plugins.sample_plugins.PluginSample"]

    urls = register_plugins_urls()

    assert len(urls) == 1
    plugin_resolver = urls[0]
    assert len(plugin_resolver.url_patterns) == 2

    # direct call on index list because we know position of the patterns.
    test_request = plugin_resolver.url_patterns[0]
    test_request_detail = plugin_resolver.url_patterns[1]

    assert test_request.lookup_str == (
        "tests.plugins.sample_plugins.PluginSample."
        "register_urls.<locals>.handle_request"
    )
    assert test_request_detail.lookup_str == (
        "tests.plugins.sample_plugins.PluginSample."
        "register_urls.<locals>.handle_detail_request"
    )


def test_test_register_plugins_urls_plugins_without_urls(settings):
    settings.PLUGINS = ["tests.plugins.sample_plugins.ActivePlugin"]
    urls = register_plugins_urls()
    assert len(urls) == 0
