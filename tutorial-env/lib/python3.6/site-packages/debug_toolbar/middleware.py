"""
Debug Toolbar middleware
"""

from __future__ import absolute_import, unicode_literals

import re
import threading

from django.conf import settings
from django.utils import six
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import force_text
from django.utils.lru_cache import lru_cache
from django.utils.module_loading import import_string

from debug_toolbar import settings as dt_settings
from debug_toolbar.toolbar import DebugToolbar

_HTML_TYPES = ("text/html", "application/xhtml+xml")


def show_toolbar(request):
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    if request.META.get("REMOTE_ADDR", None) not in settings.INTERNAL_IPS:
        return False

    return bool(settings.DEBUG)


@lru_cache()
def get_show_toolbar():
    # If SHOW_TOOLBAR_CALLBACK is a string, which is the recommended
    # setup, resolve it to the corresponding callable.
    func_or_path = dt_settings.get_config()["SHOW_TOOLBAR_CALLBACK"]
    if isinstance(func_or_path, six.string_types):
        return import_string(func_or_path)
    else:
        return func_or_path


class DebugToolbarMiddleware(MiddlewareMixin):
    """
    Middleware to set up Debug Toolbar on incoming request and render toolbar
    on outgoing response.
    """

    debug_toolbars = {}

    def process_request(self, request):
        # Decide whether the toolbar is active for this request.
        show_toolbar = get_show_toolbar()
        if not show_toolbar(request):
            return

        # Don't render the toolbar during AJAX requests.
        if request.is_ajax():
            return

        toolbar = DebugToolbar(request)
        self.__class__.debug_toolbars[threading.current_thread().ident] = toolbar

        # Activate instrumentation ie. monkey-patch.
        for panel in toolbar.enabled_panels:
            panel.enable_instrumentation()

        # Run process_request methods of panels like Django middleware.
        response = None
        for panel in toolbar.enabled_panels:
            response = panel.process_request(request)
            if response:
                break
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        toolbar = self.__class__.debug_toolbars.get(threading.current_thread().ident)
        if not toolbar:
            return

        # Run process_view methods of panels like Django middleware.
        response = None
        for panel in toolbar.enabled_panels:
            response = panel.process_view(request, view_func, view_args, view_kwargs)
            if response:
                break
        return response

    def process_response(self, request, response):
        toolbar = self.__class__.debug_toolbars.pop(
            threading.current_thread().ident, None
        )
        if not toolbar:
            return response

        # Run process_response methods of panels like Django middleware.
        for panel in reversed(toolbar.enabled_panels):
            new_response = panel.process_response(request, response)
            if new_response:
                response = new_response

        # Deactivate instrumentation ie. monkey-unpatch. This must run
        # regardless of the response. Keep 'return' clauses below.
        # (NB: Django's model for middleware doesn't guarantee anything.)
        for panel in reversed(toolbar.enabled_panels):
            panel.disable_instrumentation()

        # Check for responses where the toolbar can't be inserted.
        content_encoding = response.get("Content-Encoding", "")
        content_type = response.get("Content-Type", "").split(";")[0]
        if any(
            (
                getattr(response, "streaming", False),
                "gzip" in content_encoding,
                content_type not in _HTML_TYPES,
            )
        ):
            return response

        # Collapse the toolbar by default if SHOW_COLLAPSED is set.
        if toolbar.config["SHOW_COLLAPSED"] and "djdt" not in request.COOKIES:
            response.set_cookie("djdt", "hide", 864000)

        # Insert the toolbar in the response.
        content = force_text(response.content, encoding=response.charset)
        insert_before = dt_settings.get_config()["INSERT_BEFORE"]
        pattern = re.escape(insert_before)
        bits = re.split(pattern, content, flags=re.IGNORECASE)
        if len(bits) > 1:
            # When the toolbar will be inserted for sure, generate the stats.
            for panel in reversed(toolbar.enabled_panels):
                panel.generate_stats(request, response)
                panel.generate_server_timing(request, response)

            response = self.generate_server_timing_header(
                response, toolbar.enabled_panels
            )

            bits[-2] += toolbar.render_toolbar()
            response.content = insert_before.join(bits)
            if response.get("Content-Length", None):
                response["Content-Length"] = len(response.content)
        return response

    @staticmethod
    def generate_server_timing_header(response, panels):
        data = []

        for panel in panels:
            stats = panel.get_server_timing_stats()
            if not stats:
                continue

            for key, record in stats.items():
                # example: `SQLPanel_sql_time=0; "SQL 0 queries"`
                data.append(
                    '{}_{}={}; "{}"'.format(
                        panel.panel_id, key, record.get("value"), record.get("title")
                    )
                )

        if data:
            response["Server-Timing"] = ", ".join(data)
        return response
