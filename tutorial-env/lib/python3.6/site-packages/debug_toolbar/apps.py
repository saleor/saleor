from __future__ import absolute_import, unicode_literals

import inspect

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Warning, register
from django.middleware.gzip import GZipMiddleware
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _


class DebugToolbarConfig(AppConfig):
    name = "debug_toolbar"
    verbose_name = _("Debug Toolbar")


@register
def check_middleware(app_configs, **kwargs):
    from debug_toolbar.middleware import DebugToolbarMiddleware

    errors = []
    gzip_index = None
    debug_toolbar_indexes = []

    setting = getattr(settings, "MIDDLEWARE", None)
    setting_name = "MIDDLEWARE"
    if setting is None:
        setting = settings.MIDDLEWARE_CLASSES
        setting_name = "MIDDLEWARE_CLASSES"

    # Determine the indexes which gzip and/or the toolbar are installed at
    for i, middleware in enumerate(setting):
        if is_middleware_class(GZipMiddleware, middleware):
            gzip_index = i
        elif is_middleware_class(DebugToolbarMiddleware, middleware):
            debug_toolbar_indexes.append(i)

    if not debug_toolbar_indexes:
        # If the toolbar does not appear, report an error.
        errors.append(
            Warning(
                "debug_toolbar.middleware.DebugToolbarMiddleware is missing "
                "from %s." % setting_name,
                hint="Add debug_toolbar.middleware.DebugToolbarMiddleware to "
                "%s." % setting_name,
                id="debug_toolbar.W001",
            )
        )
    elif len(debug_toolbar_indexes) != 1:
        # If the toolbar appears multiple times, report an error.
        errors.append(
            Warning(
                "debug_toolbar.middleware.DebugToolbarMiddleware occurs "
                "multiple times in %s." % setting_name,
                hint="Load debug_toolbar.middleware.DebugToolbarMiddleware only "
                "once in %s." % setting_name,
                id="debug_toolbar.W002",
            )
        )
    elif gzip_index is not None and debug_toolbar_indexes[0] < gzip_index:
        # If the toolbar appears before the gzip index, report an error.
        errors.append(
            Warning(
                "debug_toolbar.middleware.DebugToolbarMiddleware occurs before "
                "django.middleware.gzip.GZipMiddleware in %s." % setting_name,
                hint="Move debug_toolbar.middleware.DebugToolbarMiddleware to "
                "after django.middleware.gzip.GZipMiddleware in %s." % setting_name,
                id="debug_toolbar.W003",
            )
        )

    return errors


def is_middleware_class(middleware_class, middleware_path):
    try:
        middleware_cls = import_string(middleware_path)
    except ImportError:
        return
    return inspect.isclass(middleware_cls) and issubclass(
        middleware_cls, middleware_class
    )
