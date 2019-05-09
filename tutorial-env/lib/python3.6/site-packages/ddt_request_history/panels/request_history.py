from __future__ import absolute_import, unicode_literals

import json
import logging
import os
import threading
import sys
import uuid

import debug_toolbar

from datetime import datetime
from distutils.version import LooseVersion

from django.conf import settings
from django.http import HttpResponse
from django.template import Template
from django.template.backends.django import DjangoTemplates
from django.template.context import Context
from django.utils.translation import ugettext_lazy as _

from debug_toolbar.toolbar import DebugToolbar
from debug_toolbar.panels import Panel

try:
    from collections import OrderedDict, Callable
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

try:
    toolbar_version = LooseVersion(debug_toolbar.VERSION)
except:
    toolbar_version = LooseVersion('0')

logger = logging.getLogger(__name__)

DEBUG_TOOLBAR_URL_PREFIX = getattr(settings, 'DEBUG_TOOLBAR_URL_PREFIX', '/__debug__')


try:
    from debug_toolbar.settings import get_config
    CONFIG = get_config()
except ImportError:
    from debug_toolbar.settings import CONFIG


def patched_process_request(self, request):
    # Decide whether the toolbar is active for this request.
    show_toolbar = debug_toolbar.middleware.get_show_toolbar()
    if not show_toolbar(request):
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


def patch_middleware_process_request():
    if not this_module.middleware_patched:
        if toolbar_version >= LooseVersion('1.8'):
            try:
                from debug_toolbar.middleware import DebugToolbarMiddleware
                DebugToolbarMiddleware.process_request = patched_process_request
            except ImportError:
                return
        this_module.middleware_patched = True


middleware_patched = False
template = None
this_module = sys.modules[__name__]

# XXX: need to call this as early as possible but we have circular imports when
# running with gunicorn so also try a second later
patch_middleware_process_request()
threading.Timer(1.0, patch_middleware_process_request, ()).start()


def get_template():
    if this_module.template is None:
        template_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'request_history.html'
        )
        with open(template_path) as template_file:
            this_module.template = Template(
                template_file.read(),
                engine=DjangoTemplates({'NAME': 'rh', 'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}).engine
        )
    return this_module.template


def allow_ajax(request):
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    if request.META.get('REMOTE_ADDR', None) not in settings.INTERNAL_IPS:
        return False
    if toolbar_version < LooseVersion('1.8') \
            and request.get_full_path().startswith(DEBUG_TOOLBAR_URL_PREFIX) \
            and request.GET.get('panel_id', None) != 'RequestHistoryPanel':
        return False
    return bool(settings.DEBUG)


def patched_store(self):
    if self.store_id:  # don't save if already have
        return
    self.store_id = uuid.uuid4().hex
    cls = type(self)
    cls._store[self.store_id] = self
    store_size = CONFIG.get('RESULTS_CACHE_SIZE', CONFIG.get('RESULTS_STORE_SIZE', 10))
    for dummy in range(len(cls._store) - store_size):
        try:
            # collections.OrderedDict
            cls._store.popitem(last=False)
        except TypeError:
            # django.utils.datastructures.SortedDict
            del cls._store[cls._store.keyOrder[0]]


def patched_fetch(cls, store_id):
    return cls._store.get(store_id)


DebugToolbar.store = patched_store
DebugToolbar.fetch = classmethod(patched_fetch)


class RequestHistoryPanel(Panel):
    """ A panel to display Request History """

    title = _("Request History")

    template = 'request_history.html'

    @property
    def nav_subtitle(self):
        return self.get_stats().get('request_url', '')

    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            if view_func == debug_toolbar.views.render_panel and \
                    request.GET.get('panel_id', None) == self.panel_id:
                return HttpResponse(self.content)
        except AttributeError:
            pass

    def process_response(self, request, response):
        self.record_stats({
            'request_url': request.get_full_path(),
            'request_method': request.method,
            'post': json.dumps((request.POST), sort_keys=True, indent=4),
            'time': datetime.now(),
        })

        for panel in reversed(self.toolbar.enabled_panels):
            panel.disable_instrumentation()

        # XXX: generate_stats will be called twice on requests where the toolbar is added to the page
        #   e.g. non-ajax requests. This should only cause the stats to be overwritten with the same data.
        for panel in reversed(self.toolbar.enabled_panels):
            if hasattr(panel, 'generate_stats'):
                panel.generate_stats(request, response)

                # XXX: ignore future calls to generate_stats for SQLPanel. Could probably do this for all
                #   panels but will limit it for now in case something happens in later on in the toolbar
                #   middleware.
                if panel.panel_id == 'SQLPanel':
                    panel.generate_stats = lambda a, b: None

    @property
    def content(self):
        """ Content of the panel when it's displayed in full screen. """
        toolbars = OrderedDict()
        for id, toolbar in DebugToolbar._store.items():
            content = {}
            for panel in toolbar.panels:
                panel_id = None
                nav_title = ''
                nav_subtitle = ''
                try:
                    panel_id = panel.panel_id
                    nav_title = panel.nav_title
                    nav_subtitle = panel.nav_subtitle() if isinstance(
                        panel.nav_subtitle, Callable) else panel.nav_subtitle
                except Exception:
                    logger.debug('Error parsing panel info:', exc_info=True)
                if panel_id is not None:
                    content.update({
                        panel_id: {
                            'panel_id': panel_id,
                            'nav_title': nav_title,
                            'nav_subtitle': nav_subtitle,
                        }
                    })
            toolbars[id] = {
                'toolbar': toolbar,
                'content': content
            }
        return get_template().render(Context({
            'toolbars': OrderedDict(reversed(list(toolbars.items()))),
            'trunc_length': CONFIG.get('RH_POST_TRUNC_LENGTH', 0)
        }))

    def disable_instrumentation(self):
        if not self.toolbar.stats[self.panel_id]['request_url'].startswith(DEBUG_TOOLBAR_URL_PREFIX):
            self.toolbar.store()
