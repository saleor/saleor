import importlib
from typing import List

from django.conf import settings

from .plugin import BasePlugin


class PluginError(BaseException):
    """ Default plugin exception """


class BaseManager(BasePlugin):
    """Base manager for handling a plugins logic. It inherits BasePlugin to support
    IDEs' hints"""

    plugins = None

    def __init__(self, plugins: List[str]):
        self.plugins = []
        for plugin_path in plugins:
            plugin_path, _, plugin_name = plugin_path.rpartition(".")
            plugin_module = importlib.import_module(plugin_path)
            plugin_class = getattr(plugin_module, plugin_name)
            self.plugins.append(plugin_class)

    def __getattribute__(self, item: str):
        for name, func in vars(BasePlugin).items():
            # Run custom getattribute for all plugin methods
            if name == item and not name.startswith("__"):
                return super().__getattribute__("_BaseManager__get_plugin_method")(
                    name=item
                )

        return super().__getattribute__(item)

    def __get_plugin_method(self, name: str):
        def run_plugin_method(*args, **kwargs):
            value = None
            for p in self.plugins:
                try:
                    value = getattr(p, name)(p, *args, **kwargs)
                    print(value)
                except NotImplementedError:
                    continue
                except AttributeError:
                    continue
            return value

        return run_plugin_method


def get_enabled_manager(manager_path: str = settings.EXTENSION_MANAGER) -> BaseManager:
    manager_path, _, manager_name = manager_path.rpartition(".")
    manager_module = importlib.import_module(manager_path)
    manager_class = getattr(manager_module, manager_name, None)
    return manager_class()
