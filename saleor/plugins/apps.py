from django.apps import AppConfig
from django.conf import settings
from django.utils.module_loading import import_string


class PluginConfig(AppConfig):
    name = "saleor.plugins"
    verbose_name = "Plugins"

    def ready(self):
        manager_path = settings.PLUGINS_MANAGER
        import_string(manager_path)
        plugins = settings.PLUGINS
        for plugin_path in plugins:
            import_string(plugin_path)
