from __future__ import absolute_import, unicode_literals

import warnings

from django.conf import settings
from django.utils import six
from django.utils.lru_cache import lru_cache

# Always import this module as follows:
# from debug_toolbar import settings [as dt_settings]

# Don't import directly CONFIG or PANELs, or you will miss changes performed
# with override_settings in tests.


CONFIG_DEFAULTS = {
    # Toolbar options
    "DISABLE_PANELS": {"debug_toolbar.panels.redirects.RedirectsPanel"},
    "INSERT_BEFORE": "</body>",
    "RENDER_PANELS": None,
    "RESULTS_CACHE_SIZE": 10,
    "ROOT_TAG_EXTRA_ATTRS": "",
    "SHOW_COLLAPSED": False,
    "SHOW_TOOLBAR_CALLBACK": "debug_toolbar.middleware.show_toolbar",
    # Panel options
    "EXTRA_SIGNALS": [],
    "ENABLE_STACKTRACES": True,
    "HIDE_IN_STACKTRACES": (
        "socketserver" if six.PY3 else "SocketServer",
        "threading",
        "wsgiref",
        "debug_toolbar",
        "django.db",
        "django.core.handlers",
        "django.core.servers",
        "django.utils.decorators",
        "django.utils.deprecation",
        "django.utils.functional",
    ),
    "PROFILER_MAX_DEPTH": 10,
    "SHOW_TEMPLATE_CONTEXT": True,
    "SKIP_TEMPLATE_PREFIXES": ("django/forms/widgets/", "admin/widgets/"),
    "SQL_WARNING_THRESHOLD": 500,  # milliseconds
}


@lru_cache()
def get_config():
    USER_CONFIG = getattr(settings, "DEBUG_TOOLBAR_CONFIG", {})

    # Backward-compatibility for 1.0, remove in 2.0.
    _RENAMED_CONFIG = {
        "RESULTS_STORE_SIZE": "RESULTS_CACHE_SIZE",
        "ROOT_TAG_ATTRS": "ROOT_TAG_EXTRA_ATTRS",
        "HIDDEN_STACKTRACE_MODULES": "HIDE_IN_STACKTRACES",
    }
    for old_name, new_name in _RENAMED_CONFIG.items():
        if old_name in USER_CONFIG:
            warnings.warn(
                "%r was renamed to %r. Update your DEBUG_TOOLBAR_CONFIG "
                "setting." % (old_name, new_name),
                DeprecationWarning,
            )
            USER_CONFIG[new_name] = USER_CONFIG.pop(old_name)

    if "HIDE_DJANGO_SQL" in USER_CONFIG:
        warnings.warn(
            "HIDE_DJANGO_SQL was removed. Update your " "DEBUG_TOOLBAR_CONFIG setting.",
            DeprecationWarning,
        )
        USER_CONFIG.pop("HIDE_DJANGO_SQL")

    if "TAG" in USER_CONFIG:
        warnings.warn(
            "TAG was replaced by INSERT_BEFORE. Update your "
            "DEBUG_TOOLBAR_CONFIG setting.",
            DeprecationWarning,
        )
        USER_CONFIG["INSERT_BEFORE"] = "</%s>" % USER_CONFIG.pop("TAG")

    CONFIG = CONFIG_DEFAULTS.copy()
    CONFIG.update(USER_CONFIG)

    if "INTERCEPT_REDIRECTS" in USER_CONFIG:
        warnings.warn(
            "INTERCEPT_REDIRECTS is deprecated. Please use the "
            "DISABLE_PANELS config in the "
            "DEBUG_TOOLBAR_CONFIG setting.",
            DeprecationWarning,
        )
        if USER_CONFIG["INTERCEPT_REDIRECTS"]:
            if (
                "debug_toolbar.panels.redirects.RedirectsPanel"
                in CONFIG["DISABLE_PANELS"]
            ):
                # RedirectsPanel should be enabled
                try:
                    CONFIG["DISABLE_PANELS"].remove(
                        "debug_toolbar.panels.redirects.RedirectsPanel"
                    )
                except KeyError:
                    # We wanted to remove it, but it didn't exist. This is fine
                    pass
        elif (
            "debug_toolbar.panels.redirects.RedirectsPanel"
            not in CONFIG["DISABLE_PANELS"]
        ):
            # RedirectsPanel should be disabled
            CONFIG["DISABLE_PANELS"].add(
                "debug_toolbar.panels.redirects.RedirectsPanel"
            )

    return CONFIG


PANELS_DEFAULTS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
]


@lru_cache()
def get_panels():
    try:
        PANELS = list(settings.DEBUG_TOOLBAR_PANELS)
    except AttributeError:
        PANELS = PANELS_DEFAULTS
    else:
        # Backward-compatibility for 1.0, remove in 2.0.
        _RENAMED_PANELS = {
            "debug_toolbar.panels.version.VersionDebugPanel": "debug_toolbar.panels.versions.VersionsPanel",  # noqa
            "debug_toolbar.panels.timer.TimerDebugPanel": "debug_toolbar.panels.timer.TimerPanel",  # noqa
            "debug_toolbar.panels.settings_vars.SettingsDebugPanel": "debug_toolbar.panels.settings.SettingsPanel",  # noqa
            "debug_toolbar.panels.headers.HeaderDebugPanel": "debug_toolbar.panels.headers.HeadersPanel",  # noqa
            "debug_toolbar.panels.request_vars.RequestVarsDebugPanel": "debug_toolbar.panels.request.RequestPanel",  # noqa
            "debug_toolbar.panels.sql.SQLDebugPanel": "debug_toolbar.panels.sql.SQLPanel",  # noqa
            "debug_toolbar.panels.template.TemplateDebugPanel": "debug_toolbar.panels.templates.TemplatesPanel",  # noqa
            "debug_toolbar.panels.cache.CacheDebugPanel": "debug_toolbar.panels.cache.CachePanel",  # noqa
            "debug_toolbar.panels.signals.SignalDebugPanel": "debug_toolbar.panels.signals.SignalsPanel",  # noqa
            "debug_toolbar.panels.logger.LoggingDebugPanel": "debug_toolbar.panels.logging.LoggingPanel",  # noqa
            "debug_toolbar.panels.redirects.InterceptRedirectsDebugPanel": "debug_toolbar.panels.redirects.RedirectsPanel",  # noqa
            "debug_toolbar.panels.profiling.ProfilingDebugPanel": "debug_toolbar.panels.profiling.ProfilingPanel",  # noqa
        }
        for index, old_panel in enumerate(PANELS):
            new_panel = _RENAMED_PANELS.get(old_panel)
            if new_panel is not None:
                warnings.warn(
                    "%r was renamed to %r. Update your DEBUG_TOOLBAR_PANELS "
                    "setting." % (old_panel, new_panel),
                    DeprecationWarning,
                )
                PANELS[index] = new_panel
    return PANELS
