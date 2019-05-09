"""
raven.contrib.django.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Acts as an implicit hook for Django installs.

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
# flake8: noqa

from __future__ import absolute_import, unicode_literals

import logging
import sys
import warnings

import django
from django.conf import settings
from django.core.signals import got_request_exception, request_started
from threading import Lock

from raven.utils.conf import convert_options
from raven.utils.compat import PY2, binary_type, text_type
from raven.utils.imports import import_string

logger = logging.getLogger('sentry.errors.client')


def get_installed_apps():
    """
    Modules in settings.INSTALLED_APPS as a set.
    """
    return set(settings.INSTALLED_APPS)


_client = (None, None)


class ProxyClient(object):
    """
    A proxy which represents the currently client at all times.
    """
    # introspection support:
    __members__ = property(lambda x: x.__dir__())

    # Need to pretend to be the wrapped class, for the sake of objects that care
    # about this (especially in equality tests)
    __class__ = property(lambda x: get_client().__class__)

    __dict__ = property(lambda o: get_client().__dict__)

    __repr__ = lambda x: repr(get_client())
    __getattr__ = lambda x, o: getattr(get_client(), o)
    __setattr__ = lambda x, o, v: setattr(get_client(), o, v)
    __delattr__ = lambda x, o: delattr(get_client(), o)

    __lt__ = lambda x, o: get_client() < o
    __le__ = lambda x, o: get_client() <= o
    __eq__ = lambda x, o: get_client() == o
    __ne__ = lambda x, o: get_client() != o
    __gt__ = lambda x, o: get_client() > o
    __ge__ = lambda x, o: get_client() >= o
    if PY2:
        __cmp__ = lambda x, o: cmp(get_client(), o)  # NOQA
    __hash__ = lambda x: hash(get_client())
    # attributes are currently not callable
    # __call__ = lambda x, *a, **kw: get_client()(*a, **kw)
    __nonzero__ = lambda x: bool(get_client())
    __len__ = lambda x: len(get_client())
    __getitem__ = lambda x, i: get_client()[i]
    __iter__ = lambda x: iter(get_client())
    __contains__ = lambda x, i: i in get_client()
    __getslice__ = lambda x, i, j: get_client()[i:j]
    __add__ = lambda x, o: get_client() + o
    __sub__ = lambda x, o: get_client() - o
    __mul__ = lambda x, o: get_client() * o
    __floordiv__ = lambda x, o: get_client() // o
    __mod__ = lambda x, o: get_client() % o
    __divmod__ = lambda x, o: get_client().__divmod__(o)
    __pow__ = lambda x, o: get_client() ** o
    __lshift__ = lambda x, o: get_client() << o
    __rshift__ = lambda x, o: get_client() >> o
    __and__ = lambda x, o: get_client() & o
    __xor__ = lambda x, o: get_client() ^ o
    __or__ = lambda x, o: get_client() | o
    __div__ = lambda x, o: get_client().__div__(o)
    __truediv__ = lambda x, o: get_client().__truediv__(o)
    __neg__ = lambda x: -(get_client())
    __pos__ = lambda x: +(get_client())
    __abs__ = lambda x: abs(get_client())
    __invert__ = lambda x: ~(get_client())
    __complex__ = lambda x: complex(get_client())
    __int__ = lambda x: int(get_client())
    if PY2:
        __long__ = lambda x: long(get_client())  # NOQA
    __float__ = lambda x: float(get_client())
    __str__ = lambda x: binary_type(get_client())
    __unicode__ = lambda x: text_type(get_client())
    __oct__ = lambda x: oct(get_client())
    __hex__ = lambda x: hex(get_client())
    __index__ = lambda x: get_client().__index__()
    __coerce__ = lambda x, o: x.__coerce__(x, o)
    __enter__ = lambda x: x.__enter__()
    __exit__ = lambda x, *a, **kw: x.__exit__(*a, **kw)

client = ProxyClient()


def get_client(client=None, reset=False):
    global _client

    tmp_client = client is not None
    if not tmp_client:
        client = getattr(settings, 'SENTRY_CLIENT', 'raven.contrib.django.DjangoClient')

    if _client[0] != client or reset:
        options = convert_options(
            settings,
            defaults={
                'include_paths': get_installed_apps(),
            },
        )

        try:
            Client = import_string(client)
        except ImportError:
            logger.exception('Failed to import client: %s', client)
            if not _client[1]:
                # If there is no previous client, set the default one.
                client = 'raven.contrib.django.DjangoClient'
                _client = (client, get_client(client))
        else:
            instance = Client(**options)
            if not tmp_client:
                _client = (client, instance)
            return instance
    return _client[1]


def sentry_exception_handler(request=None, **kwargs):
    try:
        client.captureException(exc_info=sys.exc_info(), request=request)
    except Exception as exc:
        try:
            logger.exception('Unable to process log entry: %s' % (exc,))
        except Exception as exc:
            warnings.warn('Unable to process log entry: %s' % (exc,))


class SentryDjangoHandler(object):
    def __init__(self, client=client):
        self.client = client

        try:
            import celery
        except ImportError:
            self.has_celery = False
        else:
            self.has_celery = celery.VERSION >= (2, 5)

        self.celery_handler = None

    def install_celery(self):
        from raven.contrib.celery import (
            SentryCeleryHandler, register_logger_signal
        )

        ignore_expected = getattr(settings,
                                  'SENTRY_CELERY_IGNORE_EXPECTED',
                                  False)

        self.celery_handler = SentryCeleryHandler(client,
                                                  ignore_expected=ignore_expected)\
                                                  .install()

        # try:
        #     ga = lambda x, d=None: getattr(settings, 'SENTRY_%s' % x, d)
        #     options = getattr(settings, 'RAVEN_CONFIG', {})
        #     loglevel = options.get('celery_loglevel',
        #                            ga('CELERY_LOGLEVEL', logging.ERROR))

        #     register_logger_signal(client, loglevel=loglevel)
        # except Exception:
        #     logger.exception('Failed to install Celery error handler')

    def install(self):
        request_started.connect(self.before_request, weak=False)
        got_request_exception.connect(self.exception_handler, weak=False)

        if self.has_celery:
            try:
                self.install_celery()
            except Exception:
                logger.exception('Failed to install Celery error handler')

    def uninstall(self):
        request_started.disconnect(self.before_request)
        got_request_exception.disconnect(self.exception_handler)

        if self.celery_handler:
            self.celery_handler.uninstall()

    def exception_handler(self, request=None, **kwargs):
        try:
            self.client.captureException(exc_info=sys.exc_info(), request=request)
        except Exception as exc:
            try:
                logger.exception('Unable to process log entry: %s' % (exc,))
            except Exception as exc:
                warnings.warn('Unable to process log entry: %s' % (exc,))

    def before_request(self, *args, **kwargs):
        self.client.context.activate()


def register_serializers():
    # force import so serializers can call register
    import raven.contrib.django.serializers  # NOQA


def install_middleware(middleware_name, lookup_names=None):
    """
    Install specified middleware
    """
    if lookup_names is None:
        lookup_names = (middleware_name,)
    # default settings.MIDDLEWARE is None
    middleware_attr = 'MIDDLEWARE' if getattr(settings,
                                              'MIDDLEWARE',
                                              None) is not None \
        else 'MIDDLEWARE_CLASSES'
    # make sure to get an empty tuple when attr is None
    middleware = getattr(settings, middleware_attr, ()) or ()
    if set(lookup_names).isdisjoint(set(middleware)):
        setattr(settings,
                middleware_attr,
                type(middleware)((middleware_name,)) + middleware)


_setup_lock = Lock()

_initialized = False

def initialize():
    global _initialized

    with _setup_lock:
        if _initialized:
            return

        # mark this as initialized immediatley to avoid recursive import issues
        _initialized = True

        try:
            register_serializers()
            install_middleware(
                'raven.contrib.django.middleware.SentryMiddleware',
                (
                    'raven.contrib.django.middleware.SentryMiddleware',
                    'raven.contrib.django.middleware.SentryLogMiddleware'))
            install_middleware(
                'raven.contrib.django.middleware.DjangoRestFrameworkCompatMiddleware')

            # XXX(dcramer): maybe this setting should disable ALL of this?
            if not getattr(settings, 'DISABLE_SENTRY_INSTRUMENTATION', False):
                handler = SentryDjangoHandler()
                handler.install()

            # instantiate client so hooks get registered
            get_client()  # NOQA
        except Exception:
            _initialized = False

# Django 1.7 uses ``raven.contrib.django.apps.RavenConfig``
if django.VERSION < (1, 7, 0):
    initialize()

