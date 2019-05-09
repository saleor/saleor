"""
raven.base
~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import zlib
import logging
import os
import sys
import time
import uuid
import warnings

from datetime import datetime
from inspect import isclass
from random import Random
from types import FunctionType
from threading import local

if sys.version_info >= (3, 2):
    import contextlib
else:
    import contextlib2 as contextlib

try:
    from thread import get_ident as get_thread_ident
except ImportError:
    from _thread import get_ident as get_thread_ident

import raven
from raven.conf import defaults
from raven.conf.remote import RemoteConfig
from raven.exceptions import APIError, RateLimited
from raven.utils import json, get_versions, get_auth_header, merge_dicts
from raven.utils.compat import text_type, iteritems
from raven.utils.encoding import to_unicode
from raven.utils.serializer import transform
from raven.utils.stacks import get_stack_info, iter_stack_frames
from raven.utils.transaction import TransactionStack
from raven.transport.registry import TransportRegistry, default_transports

# enforce imports to avoid obscure stacktraces with MemoryError
import raven.events  # NOQA


__all__ = ('Client',)

__excepthook__ = None

PLATFORM_NAME = 'python'

SDK_VALUE = {
    'name': 'raven-python',
    'version': raven.VERSION,
}

# singleton for the client
Raven = None

if sys.version_info >= (3, 2):
    basestring = str


def get_excepthook_client():
    return getattr(sys.excepthook, 'raven_client', None)


class ModuleProxyCache(dict):
    def __missing__(self, key):
        module, class_name = key.rsplit('.', 1)

        handler = getattr(__import__(
            module, {}, {}, [class_name]), class_name)

        self[key] = handler

        return handler


class ClientState(object):
    ONLINE = 1
    ERROR = 0

    def __init__(self):
        self.status = self.ONLINE
        self.last_check = None
        self.retry_number = 0
        self.retry_after = 0

    def should_try(self):
        if self.status == self.ONLINE:
            return True

        interval = self.retry_after or min(self.retry_number, 6) ** 2

        if time.time() - self.last_check > interval:
            return True

        return False

    def set_fail(self, retry_after=0):
        self.status = self.ERROR
        self.retry_number += 1
        self.last_check = time.time()
        self.retry_after = retry_after

    def set_success(self):
        self.status = self.ONLINE
        self.last_check = None
        self.retry_number = 0
        self.retry_after = 0

    def did_fail(self):
        return self.status == self.ERROR


class Client(object):
    """
    The base Raven client.

    Will read default configuration from the environment variable
    ``SENTRY_DSN`` if available.

    >>> from raven import Client

    >>> # Read configuration from ``os.environ['SENTRY_DSN']``
    >>> client = Client()

    >>> # Specify a DSN explicitly
    >>> client = Client(dsn='https://public_key:secret_key@sentry.local/project_id')

    >>> # Record an exception
    >>> try:
    >>>     1/0
    >>> except ZeroDivisionError:
    >>>     ident = client.get_ident(client.captureException())
    >>>     print "Exception caught; reference is %s" % ident
    """

    logger = logging.getLogger('raven')
    protocol_version = '6'

    _registry = TransportRegistry(transports=default_transports)

    def __init__(self, dsn=None, raise_send_errors=False, transport=None,
                 install_sys_hook=True, install_logging_hook=True,
                 hook_libraries=None, enable_breadcrumbs=True,
                 _random_seed=None, **options):
        global Raven

        o = options

        self._local_state = local()

        self.raise_send_errors = raise_send_errors

        # configure loggers first
        cls = self.__class__
        self.state = ClientState()
        self.logger = logging.getLogger(
            '%s.%s' % (cls.__module__, cls.__name__))
        self.error_logger = logging.getLogger('sentry.errors')
        self.uncaught_logger = logging.getLogger('sentry.errors.uncaught')

        self._transport_cache = {}
        self.set_dsn(dsn, transport)

        self.include_paths = set(o.get('include_paths') or [])
        self.exclude_paths = set(o.get('exclude_paths') or [])
        self.name = text_type(
            o.get('name') or os.environ.get('SENTRY_NAME') or
            o.get('machine') or defaults.NAME)
        self.auto_log_stacks = bool(
            o.get('auto_log_stacks') or defaults.AUTO_LOG_STACKS)
        self.capture_locals = bool(
            o.get('capture_locals', defaults.CAPTURE_LOCALS))
        self.string_max_length = int(
            o.get('string_max_length') or defaults.MAX_LENGTH_STRING)
        self.list_max_length = int(
            o.get('list_max_length') or defaults.MAX_LENGTH_LIST)
        self.site = o.get('site')
        self.include_versions = o.get('include_versions', True)
        self.processors = o.get('processors')
        self.sanitize_keys = o.get('sanitize_keys')
        if self.processors is None:
            self.processors = defaults.PROCESSORS

        context = o.get('context')
        if context is None:
            context = {'sys.argv': getattr(sys, 'argv', [])[:]}
        self.extra = context
        self.tags = o.get('tags') or {}
        self.environment = (
            o.get('environment') or os.environ.get('SENTRY_ENVIRONMENT', None))
        self.release = (
            o.get('release') or os.environ.get('SENTRY_RELEASE') or
            os.environ.get('HEROKU_SLUG_COMMIT'))
        self.repos = self._format_repos(o.get('repos'))
        self.sample_rate = (
            o.get('sample_rate')
            if o.get('sample_rate') is not None
            else 1
        )
        self.transaction = TransactionStack()
        self.ignore_exceptions = set(o.get('ignore_exceptions') or ())

        self.module_cache = ModuleProxyCache()

        self._random = Random(_random_seed)

        if not self.is_enabled():
            self.logger.info(
                'Raven is not configured (logging is disabled). Please see the'
                ' documentation for more information.')

        if Raven is None:
            Raven = self

        # We want to remember the creating thread id here because this
        # comes in useful for the context special handling
        self.main_thread_id = get_thread_ident()
        self.enable_breadcrumbs = enable_breadcrumbs

        from raven.context import Context
        self._context = Context(self)

        if install_sys_hook:
            self.install_sys_hook()

        if install_logging_hook:
            self.install_logging_hook()

        self.hook_libraries(hook_libraries)

    def _format_repos(self, value):
        result = {}
        if value:
            for path, config in iteritems(value):
                if path[0] != '/':
                    # assume its a module
                    path = os.path.abspath(__import__(path).__file__)
                result[path] = config
        return result

    def set_dsn(self, dsn=None, transport=None):
        if not dsn and os.environ.get('SENTRY_DSN'):
            msg = "Configuring Raven from environment variable 'SENTRY_DSN'"
            self.logger.debug(msg)
            dsn = os.environ['SENTRY_DSN']

        if dsn not in self._transport_cache:
            if not dsn:
                result = RemoteConfig(transport=transport)
            else:
                result = RemoteConfig.from_string(
                    dsn,
                    transport=transport,
                    transport_registry=self._registry,
                )
            self._transport_cache[dsn] = result
            self.remote = result
        else:
            self.remote = self._transport_cache[dsn]

        self.logger.debug("Configuring Raven for host: {0}".format(self.remote))

    def install_sys_hook(self):
        global __excepthook__

        if __excepthook__ is None:
            __excepthook__ = sys.excepthook

        def handle_exception(*exc_info):
            self.captureException(exc_info=exc_info, level='fatal')
            __excepthook__(*exc_info)
        handle_exception.raven_client = self
        sys.excepthook = handle_exception

    def install_logging_hook(self):
        from raven.breadcrumbs import install_logging_hook
        install_logging_hook()

    def hook_libraries(self, libraries):
        from raven.breadcrumbs import hook_libraries
        hook_libraries(libraries)

    @classmethod
    def register_scheme(cls, scheme, transport_class):
        cls._registry.register_scheme(scheme, transport_class)

    def get_processors(self):
        for processor in self.processors:
            yield self.module_cache[processor](self)

    def get_module_versions(self):
        if not self.include_versions:
            return {}

        version_info = sys.version_info

        modules = get_versions(self.include_paths)
        modules['python'] = '{0}.{1}.{2}'.format(
            version_info[0], version_info[1], version_info[2],
        )

        return modules

    def get_ident(self, result):
        """
        Returns a searchable string representing a message.

        >>> result = client.capture(**kwargs)
        >>> ident = client.get_ident(result)
        """
        warnings.warn('Client.get_ident is deprecated. The event ID is now '
                      'returned as the result of capture.',
                      DeprecationWarning)
        return result

    def get_handler(self, name):
        return self.module_cache[name](self)

    def get_public_dsn(self, scheme=None):
        """
        Returns a public DSN which is consumable by raven-js

        >>> # Return scheme-less DSN
        >>> print client.get_public_dsn()

        >>> # Specify a scheme to use (http or https)
        >>> print client.get_public_dsn('https')
        """
        if self.is_enabled():
            url = self.remote.get_public_dsn()
            if scheme:
                return '%s:%s' % (scheme, url)

            return url

    def _get_exception_key(self, exc_info):
        # On certain celery versions the tb_frame attribute might
        # not exist or be `None`.
        code_id = last_id = 0
        try:
            code_id = id(exc_info[2] and exc_info[2].tb_frame.f_code)
            last_id = exc_info[2] and exc_info[2].tb_lasti or 0
        except (AttributeError, IndexError):
            pass
        return (
            exc_info[0],
            id(exc_info[1]),
            code_id,
            id(exc_info[2]),
            last_id,
        )

    def skip_error_for_logging(self, exc_info):
        key = self._get_exception_key(exc_info)
        return key in self.context.exceptions_to_skip

    def record_exception_seen(self, exc_info):
        key = self._get_exception_key(exc_info)
        self.context.exceptions_to_skip.add(key)

    def build_msg(self, event_type, data=None, date=None,
                  time_spent=None, extra=None, stack=None, public_key=None,
                  tags=None, fingerprint=None, **kwargs):
        """
        Captures, processes and serializes an event into a dict object

        The result of ``build_msg`` should be a standardized dict, with
        all default values available.
        """
        # create ID client-side so that it can be passed to application
        event_id = uuid.uuid4().hex

        data = merge_dicts(self.context.data, data)

        data.setdefault('tags', {})
        data.setdefault('extra', {})

        if '.' not in event_type:
            # Assume it's a builtin
            event_type = 'raven.events.%s' % event_type

        handler = self.get_handler(event_type)
        result = handler.capture(**kwargs)

        # data (explicit) culprit takes over auto event detection
        culprit = result.pop('culprit', None)
        if data.get('culprit'):
            culprit = data['culprit']

        for k, v in iteritems(result):
            if k not in data:
                data[k] = v

        # auto_log_stacks only applies to events that are not exceptions
        # due to confusion about which stack is which and the automatic
        # application of stacktrace to exception objects by Sentry
        if stack is None and 'exception' not in data:
            stack = self.auto_log_stacks

        if stack and 'stacktrace' not in data:
            if stack is True:
                frames = iter_stack_frames()

            else:
                frames = stack

            stack_info = get_stack_info(
                frames,
                transformer=self.transform,
                capture_locals=self.capture_locals,
            )
            data.update({
                'stacktrace': stack_info,
            })

        if self.include_paths:
            for frame in self._iter_frames(data):
                if frame.get('in_app') is not None:
                    continue

                path = frame.get('module')
                if not path:
                    continue

                if path.startswith('raven.'):
                    frame['in_app'] = False
                else:
                    frame['in_app'] = (
                        any(path.startswith(x) for x in self.include_paths) and
                        not any(path.startswith(x) for x in self.exclude_paths)
                    )

        transaction = None
        if not culprit:
            transaction = self.transaction.peek()

        if not data.get('level'):
            data['level'] = kwargs.get('level') or logging.ERROR

        if not data.get('server_name'):
            data['server_name'] = self.name

        if not data.get('modules'):
            data['modules'] = self.get_module_versions()

        if self.release is not None:
            data['release'] = self.release

        if self.environment is not None:
            data['environment'] = self.environment

        data['tags'] = merge_dicts(self.tags, data['tags'], tags)
        data['extra'] = merge_dicts(self.extra, data['extra'], extra)

        # Legacy support for site attribute
        site = data.pop('site', None) or self.site
        if site:
            data['tags'].setdefault('site', site)

        if transaction:
            data['transaction'] = transaction
        elif culprit:
            data['culprit'] = culprit

        if fingerprint:
            data['fingerprint'] = fingerprint

        # Run the data through processors
        for processor in self.get_processors():
            data.update(processor.process(data))

        if 'message' not in data:
            data['message'] = kwargs.get('message', handler.to_string(data))

        # tags should only be key=>u'value'
        for key, value in iteritems(data['tags']):
            data['tags'][key] = to_unicode(value)

        # extra data can be any arbitrary value
        for k, v in iteritems(data['extra']):
            data['extra'][k] = self.transform(v)

        # It's important date is added **after** we serialize
        data.setdefault('project', self.remote.project)
        data.setdefault('timestamp', date or datetime.utcnow())
        data.setdefault('time_spent', time_spent)
        data.setdefault('event_id', event_id)
        data.setdefault('platform', PLATFORM_NAME)
        data.setdefault('sdk', SDK_VALUE)
        data.setdefault('repos', self.repos)

        # insert breadcrumbs
        if self.enable_breadcrumbs:
            crumbs = self.context.breadcrumbs.get_buffer()
            if crumbs:
                # Make sure we send the crumbs here as "values" as we use the
                # raven client internally in sentry and the alternative
                # submission option of a list here is not supported by the
                # internal sender.
                data.setdefault('breadcrumbs', {
                    'values': crumbs
                })

        return data

    def transform(self, data):
        return transform(
            data, list_max_length=self.list_max_length,
            string_max_length=self.string_max_length)

    @property
    def context(self):
        """
        Updates this clients thread-local context for future events.

        >>> def view_handler(view_func, *args, **kwargs):
        >>>     client.context.merge(tags={'key': 'value'})
        >>>     try:
        >>>         return view_func(*args, **kwargs)
        >>>     finally:
        >>>         client.context.clear()
        """
        return self._context

    def user_context(self, data):
        """
        Update the user context for future events.

        >>> client.user_context({'email': 'foo@example.com'})
        """
        return self.context.merge({
            'user': data,
        })

    def http_context(self, data, **kwargs):
        """
        Update the http context for future events.

        >>> client.http_context({'url': 'http://example.com'})
        """
        return self.context.merge({
            'request': data,
        })

    def extra_context(self, data, **kwargs):
        """
        Update the extra context for future events.

        >>> client.extra_context({'foo': 'bar'})
        """
        return self.context.merge({
            'extra': data,
        })

    def tags_context(self, data, **kwargs):
        """
        Update the tags context for future events.

        >>> client.tags_context({'version': '1.0'})

        """
        return self.context.merge({
            'tags': data,
        })

    def capture(self, event_type, data=None, date=None, time_spent=None,
                extra=None, stack=None, tags=None, sample_rate=None,
                **kwargs):
        """
        Captures and processes an event and pipes it off to SentryClient.send.

        To use structured data (interfaces) with capture:

        >>> capture('raven.events.Message', message='foo', data={
        >>>     'request': {
        >>>         'url': '...',
        >>>         'data': {},
        >>>         'query_string': '...',
        >>>         'method': 'POST',
        >>>     },
        >>>     'logger': 'logger.name',
        >>> }, extra={
        >>>     'key': 'value',
        >>> })

        The finalized ``data`` structure contains the following (some optional)
        builtin values:

        >>> {
        >>>     # the culprit and version information
        >>>     'culprit': 'full.module.name', # or /arbitrary/path
        >>>
        >>>     # all detectable installed modules
        >>>     'modules': {
        >>>         'full.module.name': 'version string',
        >>>     },
        >>>
        >>>     # arbitrary data provided by user
        >>>     'extra': {
        >>>         'key': 'value',
        >>>     }
        >>> }

        :param event_type: the module path to the Event class. Builtins can use
                           shorthand class notation and exclude the full module
                           path.
        :param data: the data base, useful for specifying structured data
                           interfaces. Any key which contains a '.' will be
                           assumed to be a data interface.
        :param date: the datetime of this event
        :param time_spent: a integer value representing the duration of the
                           event (in milliseconds)
        :param extra: a dictionary of additional standard metadata
        :param stack: a stacktrace for the event
        :param tags: dict of extra tags
        :param sample_rate: a float in the range [0, 1] to sample this message
        :return: a 32-length string identifying this event
        """
        if not self.is_enabled():
            return

        exc_info = kwargs.get('exc_info')
        if exc_info is not None:
            if self.skip_error_for_logging(exc_info):
                return
            elif not self.should_capture(exc_info):
                self.logger.info(
                    'Not capturing exception due to filters: %s', exc_info[0],
                    exc_info=sys.exc_info())
                return
            self.record_exception_seen(exc_info)

        data = self.build_msg(
            event_type, data, date, time_spent, extra, stack, tags=tags,
            **kwargs)

        # should this event be sampled?
        if sample_rate is None:
            sample_rate = self.sample_rate

        if self._random.random() < sample_rate:
            self.send(**data)

        self._local_state.last_event_id = data['event_id']

        return data['event_id']

    def is_enabled(self):
        """
        Return a boolean describing whether the client should attempt to send
        events.
        """
        return self.remote.is_active()

    def _iter_frames(self, data):
        if 'stacktrace' in data:
            for frame in data['stacktrace']['frames']:
                yield frame
        if 'exception' in data:
            for frame in data['exception']['values'][-1]['stacktrace'].get('frames', []):
                yield frame

    def _successful_send(self):
        self.state.set_success()

    def _failed_send(self, exc, url, data):
        retry_after = 0
        if isinstance(exc, APIError):
            if isinstance(exc, RateLimited):
                retry_after = exc.retry_after
            self.error_logger.error(
                'Sentry responded with an API error: %s(%s)',
                type(exc).__name__, exc.message)
        else:
            self.error_logger.error(
                'Sentry responded with an error: %s (url: %s)',
                exc, url,
                exc_info=True,
                extra={'data': data}
            )

        self._log_failed_submission(data)
        self.state.set_fail(retry_after=retry_after)

    def _log_failed_submission(self, data):
        """
        Log a reasonable representation of an event that should have been sent
        to Sentry
        """
        message = data.pop('message', '<no message value>')
        output = [message]
        if 'exception' in data and 'stacktrace' in data['exception']['values'][-1]:
            # try to reconstruct a reasonable version of the exception
            for frame in data['exception']['values'][-1]['stacktrace'].get('frames', []):
                output.append('  File "%(fn)s", line %(lineno)s, in %(func)s' % {
                    'fn': frame.get('filename', 'unknown_filename'),
                    'lineno': frame.get('lineno', -1),
                    'func': frame.get('function', 'unknown_function'),
                })

        self.uncaught_logger.error(output)

    def send_remote(self, url, data, headers=None):
        # If the client is configured to raise errors on sending,
        # the implication is that the backoff and retry strategies
        # will be handled by the calling application
        if headers is None:
            headers = {}

        if not self.raise_send_errors and not self.state.should_try():
            data = self.decode(data)
            self._log_failed_submission(data)
            return

        self.logger.debug('Sending message of length %d to %s', len(data), url)

        def failed_send(e):
            self._failed_send(e, url, self.decode(data))

        try:
            transport = self.remote.get_transport()
            if transport.is_async:
                transport.async_send(url, data, headers, self._successful_send,
                                     failed_send)
            else:
                transport.send(url, data, headers)
                self._successful_send()
        except Exception as e:
            if self.raise_send_errors:
                raise
            failed_send(e)

    def send(self, auth_header=None, **data):
        """
        Serializes the message and passes the payload onto ``send_encoded``.
        """
        message = self.encode(data)

        return self.send_encoded(message, auth_header=auth_header)

    def send_encoded(self, message, auth_header=None, **kwargs):
        """
        Given an already serialized message, signs the message and passes the
        payload off to ``send_remote``.
        """
        client_string = 'raven-python/%s' % (raven.VERSION,)

        if not auth_header:
            timestamp = time.time()
            auth_header = get_auth_header(
                protocol=self.protocol_version,
                timestamp=timestamp,
                client=client_string,
                api_key=self.remote.public_key,
                api_secret=self.remote.secret_key,
            )

        headers = {
            'User-Agent': client_string,
            'X-Sentry-Auth': auth_header,
            'Content-Encoding': self.get_content_encoding(),
            'Content-Type': 'application/octet-stream',
        }

        return self.send_remote(
            url=self.remote.store_endpoint,
            data=message,
            headers=headers,
            **kwargs
        )

    def get_content_encoding(self):
        return 'deflate'

    def encode(self, data):
        """
        Serializes ``data`` into a raw string.
        """
        return zlib.compress(json.dumps(data).encode('utf8'))

    def decode(self, data):
        """
        Unserializes a string, ``data``.
        """
        return json.loads(zlib.decompress(data).decode('utf8'))

    def captureMessage(self, message, **kwargs):
        """
        Creates an event from ``message``.

        >>> client.captureMessage('My event just happened!')
        """
        return self.capture('raven.events.Message', message=message, **kwargs)

    def captureException(self, exc_info=None, **kwargs):
        """
        Creates an event from an exception.

        >>> try:
        >>>     exc_info = sys.exc_info()
        >>>     client.captureException(exc_info)
        >>> finally:
        >>>     del exc_info

        If exc_info is not provided, or is set to True, then this method will
        perform the ``exc_info = sys.exc_info()`` and the requisite clean-up
        for you.

        ``kwargs`` are passed through to ``.capture``.
        """
        if exc_info is None or exc_info is True:
            exc_info = sys.exc_info()

        return self.capture(
            'raven.events.Exception', exc_info=exc_info, **kwargs)

    def should_capture(self, exc_info):
        exc_type = exc_info[0]
        exc_name = '%s.%s' % (exc_type.__module__, exc_type.__name__)
        exclusions = self.ignore_exceptions
        string_exclusions = (e for e in exclusions if isinstance(e, basestring))
        wildcard_exclusions = (e for e in string_exclusions if e.endswith('*'))
        class_exclusions = (e for e in exclusions if isclass(e))

        if (exc_type in exclusions
                or exc_type.__name__ in exclusions
                or exc_name in exclusions
                or any(issubclass(exc_type, e) for e in class_exclusions)
                or any(exc_name.startswith(e[:-1]) for e in wildcard_exclusions)):
            return False
        return True

    def capture_exceptions(self, function_or_exceptions=None, **kwargs):
        """
        Wrap a function or code block in try/except and automatically call
        ``.captureException`` if it raises an exception, then the exception
        is reraised.

        By default, it will capture ``Exception``

        >>> @client.capture_exceptions
        >>> def foo():
        >>>     raise Exception()

        >>> with client.capture_exceptions():
        >>>    raise Exception()

        You can also specify exceptions to be caught specifically

        >>> @client.capture_exceptions((IOError, LookupError))
        >>> def bar():
        >>>     ...

        >>> with client.capture_exceptions((IOError, LookupError)):
        >>>    ...

        ``kwargs`` are passed through to ``.captureException``.
        """
        function = None
        exceptions = (Exception,)
        if isinstance(function_or_exceptions, FunctionType):
            function = function_or_exceptions
        elif function_or_exceptions is not None:
            exceptions = function_or_exceptions

        # In python3.2 contextmanager acts both as contextmanager and decorator
        @contextlib.contextmanager
        def make_decorator(exceptions):
            try:
                yield
            except exceptions:
                self.captureException(**kwargs)
                raise

        decorator = make_decorator(exceptions)

        if function:
            return decorator(function)
        return decorator

    def captureQuery(self, query, params=(), engine=None, **kwargs):
        """
        Creates an event for a SQL query.

        >>> client.captureQuery('SELECT * FROM foo')
        """
        return self.capture(
            'raven.events.Query', query=query, params=params, engine=engine,
            **kwargs)

    def captureExceptions(self, **kwargs):
        warnings.warn(
            'captureExceptions is deprecated, used context() instead.',
            DeprecationWarning)
        return self.context(**kwargs)

    def captureBreadcrumb(self, *args, **kwargs):
        """
        Records a breadcrumb with the current context.  They will be
        sent with the next event.
        """
        # Note: framework integration should not call this method but
        # instead use the raven.breadcrumbs.record_breadcrumb function
        # which will record to the correct client automatically.
        self.context.breadcrumbs.record(*args, **kwargs)

    capture_breadcrumb = captureBreadcrumb

    @property
    def last_event_id(self):
        return getattr(self._local_state, 'last_event_id', None)

    @last_event_id.setter
    def last_event_id(self, value):
        self._local_state.last_event_id = value


class DummyClient(Client):
    """Sends messages into an empty void."""

    def send(self, **kwargs):
        return None
