"""
raven.context
~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from collections import Mapping, Iterable
from threading import local
from weakref import ref as weakref

from raven.utils.compat import iteritems

try:
    from thread import get_ident as get_thread_ident
except ImportError:
    from _thread import get_ident as get_thread_ident


_active_contexts = local()


def get_active_contexts():
    """Returns all the active contexts for the current thread."""
    try:
        return list(_active_contexts.contexts)
    except AttributeError:
        return []


class Context(local, Mapping, Iterable):
    """
    Stores context until cleared.

    >>> def view_handler(view_func, *args, **kwargs):
    >>>     context = Context()
    >>>     context.merge(tags={'key': 'value'})
    >>>     try:
    >>>         return view_func(*args, **kwargs)
    >>>     finally:
    >>>         context.clear()
    """

    def __init__(self, client=None):
        breadcrumbs = raven.breadcrumbs.make_buffer(
            client is None or client.enable_breadcrumbs)
        if client is not None:
            client = weakref(client)
        self._client = client
        # Because the thread auto activates the thread local this also
        # means that we auto activate this thing.  Only if someone decides
        # to deactivate manually later another call to activate is
        # technically necessary.
        self.activate()
        self.data = {}
        self.exceptions_to_skip = set()
        self.breadcrumbs = breadcrumbs

    @property
    def client(self):
        if self._client is None:
            return None
        return self._client()

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return '<%s: %s>' % (type(self).__name__, self.data)

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.deactivate()

    def activate(self, sticky=False):
        if sticky:
            self._sticky_thread = get_thread_ident()
        _active_contexts.__dict__.setdefault('contexts', set()).add(self)

    def deactivate(self):
        try:
            _active_contexts.contexts.discard(self)
        except AttributeError:
            pass

    def merge(self, data, activate=True):
        if activate:
            self.activate()
        d = self.data
        for key, value in iteritems(data):
            if key in ('tags', 'extra'):
                d.setdefault(key, {})
                for t_key, t_value in iteritems(value):
                    d[key][t_key] = t_value
            else:
                d[key] = value

    def set(self, data):
        self.data = data

    def get(self):
        return self.data

    def clear(self, deactivate=None):
        self.data = {}
        self.exceptions_to_skip.clear()
        self.breadcrumbs.clear()

        # If the caller did not specify if it wants to deactivate the
        # context for the thread we only deactivate it if we're not the
        # thread that created the context (main thread).
        if deactivate is None:
            client = self.client
            if client is not None:
                deactivate = get_thread_ident() != client.main_thread_id

        if deactivate:
            self.deactivate()


import raven.breadcrumbs
