from django.conf import settings
from django.urls import include, path
from django.utils.module_loading import import_string


def register_plugins_urls():
    plugins = settings.PLUGINS
    urlpatterns = []
    for plugin_path in plugins:
        PluginClass = import_string(plugin_path)
        if not PluginClass.URL_ID:
            continue
        plugin_urls = PluginClass.register_urls()
        if not plugin_urls:
            continue
        urlpatterns.append(path(f"{PluginClass.URL_ID}/", include(plugin_urls)))
    return urlpatterns
