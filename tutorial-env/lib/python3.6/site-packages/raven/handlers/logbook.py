"""
raven.handlers.logbook
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
from __future__ import print_function

import logbook
import sys
import traceback

from raven.utils.compat import string_types
from raven.base import Client
from raven.utils.encoding import to_string


class SentryHandler(logbook.Handler):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, string_types):
                self.client = kwargs.pop('client_cls', Client)(dsn=arg, **kwargs)
            elif isinstance(arg, Client):
                self.client = arg
            else:
                raise ValueError('The first argument to %s must be either a Client instance or a DSN, got %r instead.' % (
                    self.__class__.__name__,
                    arg,
                ))
            args = []
        else:
            try:
                self.client = kwargs.pop('client')
            except KeyError:
                raise TypeError('Expected keyword argument for SentryHandler: client')
        super(SentryHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        try:
            # Avoid typical config issues by overriding loggers behavior
            if record.channel.startswith(('sentry.errors', 'raven')):
                print(to_string(self.format(record)), file=sys.stderr)
                return

            return self._emit(record)
        except Exception:
            if self.client.raise_send_errors:
                raise
            print("Top level Sentry exception caught - failed creating log record", file=sys.stderr)
            print(to_string(record.msg), file=sys.stderr)
            print(to_string(traceback.format_exc()))

            try:
                self.client.captureException()
            except Exception:
                pass

    def _emit(self, record):
        data = {
            'level': logbook.get_level_name(record.level).lower(),
            'logger': record.channel,
        }

        event_type = 'raven.events.Message'

        handler_kwargs = {
            'message': record.msg,
            'params': record.args,
            'formatted': self.format(record),
        }

        if 'tags' in record.kwargs:
            handler_kwargs['tags'] = record.kwargs['tags']

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if record.exc_info is True or (record.exc_info and all(record.exc_info)):
            handler = self.client.get_handler(event_type)
            data.update(handler.capture(**handler_kwargs))

            event_type = 'raven.events.Exception'
            handler_kwargs['exc_info'] = record.exc_info

        extra = {
            'lineno': record.lineno,
            'filename': record.filename,
            'function': record.func_name,
            'process': record.process,
            'process_name': record.process_name,
        }
        extra.update(record.extra)

        return self.client.capture(event_type,
            data=data,
            extra=extra,
            **handler_kwargs
        )
