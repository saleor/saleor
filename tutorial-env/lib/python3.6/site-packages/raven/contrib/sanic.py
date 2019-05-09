"""
raven.contrib.sanic
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2018 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging

import blinker

from raven.conf import setup_logging
from raven.base import Client
from raven.handlers.logging import SentryHandler
from raven.utils.compat import urlparse
from raven.utils.encoding import to_unicode
from raven.utils.conf import convert_options


raven_signals = blinker.Namespace()
logging_configured = raven_signals.signal('logging_configured')


def make_client(client_cls, app, dsn=None):
    return client_cls(
        **convert_options(
            app.config,
            defaults={
                'dsn': dsn,
                'include_paths': (
                    set(app.config.get('SENTRY_INCLUDE_PATHS', []))
                    | set([app.name])
                ),
                'extra': {
                    'app': app,
                },
            },
        )
    )


class Sentry(object):
    """
    Sanic application for Sentry.

    Look up configuration from ``os.environ['SENTRY_DSN']``::

    >>> sentry = Sentry(app)

    Pass an arbitrary DSN::

    >>> sentry = Sentry(app, dsn='http://public:secret@example.com/1')

    Pass an explicit client::

    >>> sentry = Sentry(app, client=client)

    Automatically configure logging::

    >>> sentry = Sentry(app, logging=True, level=logging.ERROR)

    Capture an exception::

    >>> try:
    >>>     1 / 0
    >>> except ZeroDivisionError:
    >>>     sentry.captureException()

    Capture a message::

    >>> sentry.captureMessage('hello, world!')
    """

    def __init__(self, app, client=None, client_cls=Client, dsn=None,
                 logging=False, logging_exclusions=None, level=logging.NOTSET):
        if client and not isinstance(client, Client):
            raise TypeError('client should be an instance of Client')

        self.client = client
        self.client_cls = client_cls
        self.dsn = dsn
        self.logging = logging
        self.logging_exclusions = logging_exclusions
        self.level = level
        self.init_app(app)

    def handle_exception(self, request, exception):
        if not self.client:
            return
        try:
            self.client.http_context(self.get_http_info(request))
        except Exception as e:
            self.client.logger.exception(to_unicode(e))

        # Since Sanic is restricted to Python 3, let's be explicit with what
        # we pass for exception info, rather than relying on sys.exc_info().
        exception_info = (type(exception), exception, exception.__traceback__)
        self.captureException(exc_info=exception_info)

    def get_form_data(self, request):
        return request.form

    def get_http_info(self, request):
        """
        Determine how to retrieve actual data by using request.mimetype.
        """
        if self.is_json_type(request):
            retriever = self.get_json_data
        else:
            retriever = self.get_form_data
        return self.get_http_info_with_retriever(request, retriever)

    def get_json_data(self, request):
        return request.json

    def get_http_info_with_retriever(self, request, retriever):
        """
        Exact method for getting http_info but with form data work around.
        """
        urlparts = urlparse.urlsplit(request.url)

        try:
            data = retriever(request)
        except Exception:
            data = {}

        return {
            'url': '{0}://{1}{2}'.format(
                urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': data,
            'cookies': request.cookies,
            'headers': request.headers,
            'env': {
                'REMOTE_ADDR': request.remote_addr,
            }
        }

    def is_json_type(self, request):
        content_type = request.headers.get('content-type')
        return content_type == 'application/json'

    def init_app(self, app, dsn=None, logging=None, level=None,
                 logging_exclusions=None):
        if dsn is not None:
            self.dsn = dsn

        if level is not None:
            self.level = level

        if logging is not None:
            self.logging = logging

        if logging_exclusions is None:
            self.logging_exclusions = (
                'root', 'sanic.access', 'sanic.error')
        else:
            self.logging_exclusions = logging_exclusions

        if not self.client:
            self.client = make_client(self.client_cls, app, self.dsn)

        if self.logging:
            kwargs = {}
            if self.logging_exclusions is not None:
                kwargs['exclude'] = self.logging_exclusions
            handler = SentryHandler(self.client, level=self.level)
            setup_logging(handler, **kwargs)
            logging_configured.send(
                self, sentry_handler=SentryHandler, **kwargs)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['sentry'] = self

        app.error_handler.add(Exception, self.handle_exception)
        app.register_middleware(self.before_request, attach_to='request')
        app.register_middleware(self.after_request, attach_to='response')

    def before_request(self, request):
        self.last_event_id = None
        try:
            self.client.http_context(self.get_http_info(request))
        except Exception as e:
            self.client.logger.exception(to_unicode(e))

    def after_request(self, request, response):
        if self.last_event_id:
            response.headers['X-Sentry-ID'] = self.last_event_id
        self.client.context.clear()

    def captureException(self, *args, **kwargs):
        assert self.client, 'captureException called before application configured'
        result = self.client.captureException(*args, **kwargs)
        self.set_last_event_id_from_result(result)
        return result

    def captureMessage(self, *args, **kwargs):
        assert self.client, 'captureMessage called before application configured'
        result = self.client.captureMessage(*args, **kwargs)
        self.set_last_event_id_from_result(result)
        return result

    def set_last_event_id_from_result(self, result):
        if result:
            self.last_event_id = self.client.get_ident(result)
        else:
            self.last_event_id = None

    def user_context(self, *args, **kwargs):
        assert self.client, 'user_context called before application configured'
        return self.client.user_context(*args, **kwargs)

    def tags_context(self, *args, **kwargs):
        assert self.client, 'tags_context called before application configured'
        return self.client.tags_context(*args, **kwargs)

    def extra_context(self, *args, **kwargs):
        assert self.client, 'extra_context called before application configured'
        return self.client.extra_context(*args, **kwargs)
