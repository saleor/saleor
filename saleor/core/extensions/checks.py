import importlib

from django.conf import settings
from django.core.checks import Error, register


@register()
def check_extensions(app_configs, **kwargs):
    """Confirm a correct import of plugins and manager."""
    errors = []
    if not settings.EXTENSION_MANAGER:
        return []
    manager_path = settings.EXTENSION_MANAGER
    manager_path, _, manager_name = manager_path.rpartition(".")
    manager_module = importlib.import_module(manager_path)
    manager_class = getattr(manager_module, manager_name, None)
    if not manager_class:
        errors.append(
            Error(
                "Extension Manager %s doesn't exists in specific path %s"
                % (manager_name, str(manager_module))
            )
        )

    plugins = settings.PLUGINS

    if plugins:
        for plugin_path in plugins:
            plugin_path, _, plugin_name = plugin_path.rpartition(".")
            plugin_module = importlib.import_module(plugin_path)
            plugin_class = getattr(plugin_module, plugin_name, None)
            if not plugin_class:
                errors.append(
                    Error(
                        "Plugin %s doesn't exists in specific path %s"
                        % (plugin_name, str(plugin_module))
                    )
                )
    return errors
