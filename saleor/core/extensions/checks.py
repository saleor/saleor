from typing import List

from django.conf import settings
from django.core.checks import Error, register
from django.utils.module_loading import import_string


@register()
def check_extensions(app_configs, **kwargs):
    """Confirm a correct import of plugins and manager."""
    errors = []
    check_manager(errors)

    plugins = settings.PLUGINS or []

    for plugin_path in plugins:
        check_single_plugin(plugin_path, errors)

    return errors


def check_manager(errors: List[Error]):
    if not hasattr(settings, "EXTENSIONS_MANAGER") or not settings.EXTENSIONS_MANAGER:
        errors.append(Error("Settings should contain EXTENSIONS_MANAGER env"))
        return

    try:
        import_string(settings.EXTENSIONS_MANAGER)
    except ImportError:
        errors.append(
            Error(
                "Extension Manager path: %s doesn't exist" % settings.EXTENSIONS_MANAGER
            )
        )


def check_single_plugin(plugin_path: str, errors: List[Error]):
    if not plugin_path:
        errors.append(Error("Wrong plugin_path %s" % plugin_path))
        return
    try:
        import_string(plugin_path)
    except ImportError:
        errors.append(Error("Plugin with path: %s doesn't exist" % plugin_path))
