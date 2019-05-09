import os
import sys
from importlib import import_module
import pkgutil


def get_path(module):
    if getattr(sys, 'frozen', False):
        # frozen

        if getattr(sys, '_MEIPASS', False):
            # PyInstaller
            lib_dir = getattr(sys, '_MEIPASS')
        else:
            # others
            base_dir = os.path.dirname(sys.executable)
            lib_dir = os.path.join(base_dir, "lib")

        module_to_rel_path = os.path.join(*module.__package__.split("."))
        path = os.path.join(lib_dir, module_to_rel_path)
    else:
        # unfrozen
        path = os.path.dirname(os.path.realpath(module.__file__))
    return path


def list_module(module):
    path = get_path(module)

    if getattr(sys, '_MEIPASS', False):
        # PyInstaller
        return [name for name in os.listdir(path)
                if os.path.isdir(os.path.join(path, name)) and
                "__init__.py" in os.listdir(os.path.join(path, name))]
    else:
        return [name for _, name, is_pkg in pkgutil.iter_modules([path]) if is_pkg]


def find_available_locales(providers):
    available_locales = set()

    for provider_path in providers:

        provider_module = import_module(provider_path)
        if getattr(provider_module, 'localized', False):
            langs = list_module(provider_module)
            available_locales.update(langs)
    return available_locales


def find_available_providers(modules):
    available_providers = set()
    for providers_mod in modules:
        providers = [
            '.'.join([providers_mod.__package__, mod])
            for mod in list_module(providers_mod) if mod != '__pycache__'
        ]
        available_providers.update(providers)
    return sorted(available_providers)
