import importlib
import os
from typing import List

from celery import Celery
from django.conf import settings


def discover_plugins_modules(plugins: List[str]):
    plugins_modules = []
    for dotted_path in plugins:
        try:
            module_path, class_name = dotted_path.rsplit(".", 1)
        except ValueError as err:
            raise ImportError(
                "%s doesn't look like a module path" % dotted_path
            ) from err

        module = importlib.import_module(module_path)
        plugins_modules.append(module.__package__)
    return plugins_modules


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

app = Celery("saleor")

CELERY_TIMEZONE = "UTC"

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(lambda: discover_plugins_modules(settings.PLUGINS))
