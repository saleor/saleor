from __future__ import absolute_import, unicode_literals

__all__ = ["VERSION"]


try:
    import pkg_resources

    VERSION = pkg_resources.get_distribution("django-debug-toolbar").version
except Exception:
    VERSION = "unknown"


# Code that discovers files or modules in INSTALLED_APPS imports this module.

urls = "debug_toolbar.toolbar", "djdt"

default_app_config = "debug_toolbar.apps.DebugToolbarConfig"
