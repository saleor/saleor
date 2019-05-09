"""
raven.handlers.logging
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
from __future__ import print_function

import datetime
import logging
import sys
import traceback

from raven.utils.compat import string_types, iteritems, text_type
from raven.base import Client
from raven.utils.encoding import to_string
from raven.utils.stacks import iter_stack_frames

RESERVED = frozenset((
    'stack', 'name', 'module', 'funcName', 'args', 'msg', 'levelno',
    'exc_text', 'exc_info', 'data', 'created', 'levelname', 'msecs',
    'relativeCreated', 'tags', 'message',
))


CONTEXTUAL = frozenset((
    'user', 'culprit', 'server_name', 'fingerprint'
))


def extract_extra(record, reserved=RESERVED, contextual=CONTEXTUAL):
    data = {}

    extra = getattr(record, 'data', None)
    if not isinstance(extra, dict):
        if extra:
            extra = {'data': extra}
        else:
            extra = {}
    else:
        # record.data may be something we don't want to mutate to not cause unexpected side effects
        extra = dict(extra)

    for k, v in iteritems(vars(record)):
        if k in reserved:
            continue
        if k.startswith('_'):
            continue
        if '.' not in k and k not in contextual:
            extra[k] = v
        else:
            data[k] = v

    return data, extra


class SentryHandler(logging.Handler, object):
    def __init__(self, *args, **kwargs):
        client = kwargs.get('client_cls', Client)
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, string_types):
                self.client = client(dsn=arg, **kwargs)
            elif isinstance(arg, Client):
                self.client = arg
            else:
                raise ValueError('The first argument to %s must be either a '
                                 'Client instance or a DSN, got %r instead.' %
                                 (self.__class__.__name__, arg,))
        elif 'client' in kwargs:
            self.client = kwargs['client']
        else:
            self.client = client(*args, **kwargs)

        self.tags = kwargs.pop('tags', None)

        logging.Handler.__init__(self, level=kwargs.get('level', logging.NOTSET))

    def can_record(self, record):
        return not (
            record.name == 'raven' or
            record.name.startswith(('sentry.errors', 'raven.'))
        )

    def emit(self, record):
        try:
            # Beware to python3 bug (see #10805) if exc_info is (None, None, None)
            self.format(record)

            if not self.can_record(record):
                print(to_string(record.message), file=sys.stderr)
                return

            return self._emit(record)
        except Exception:
            if self.client.raise_send_errors:
                raise
            print("Top level Sentry exception caught - failed "
                  "creating log record", file=sys.stderr)
            print(to_string(record.msg), file=sys.stderr)
            print(to_string(traceback.format_exc()), file=sys.stderr)

    def _get_targetted_stack(self, stack, record):
        # we might need to traverse this multiple times, so coerce it to a list
        stack = list(stack)
        frames = []
        started = False
        last_mod = ''

        for item in stack:
            if isinstance(item, (list, tuple)):
                frame, lineno = item
            else:
                frame, lineno = item, item.f_lineno

            if not started:
                f_globals = getattr(frame, 'f_globals', {})
                module_name = f_globals.get('__name__', '')
                if ((last_mod and last_mod.startswith('logging')) and
                        not module_name.startswith('logging')):
                    started = True
                else:
                    last_mod = module_name
                    continue

            frames.append((frame, lineno))

        # We failed to find a starting point
        if not frames:
            return stack

        return frames

    def _emit(self, record, **kwargs):
        data, extra = extract_extra(record)

        stack = getattr(record, 'stack', None)
        if stack is True:
            stack = iter_stack_frames()

        if stack:
            stack = self._get_targetted_stack(stack, record)

        date = datetime.datetime.utcfromtimestamp(record.created)
        event_type = 'raven.events.Message'
        handler_kwargs = {
            'params': record.args,
        }
        try:
            handler_kwargs['message'] = text_type(record.msg)
        except UnicodeDecodeError:
            # Handle binary strings where it should be unicode...
            handler_kwargs['message'] = repr(record.msg)[1:-1]

        try:
            handler_kwargs['formatted'] = text_type(record.message)
        except UnicodeDecodeError:
            # Handle binary strings where it should be unicode...
            handler_kwargs['formatted'] = repr(record.message)[1:-1]

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if record.exc_info and all(record.exc_info):
            # capture the standard message first so that we ensure
            # the event is recorded as an exception, in addition to having our
            # message interface attached
            handler = self.client.get_handler(event_type)
            data.update(handler.capture(**handler_kwargs))

            event_type = 'raven.events.Exception'
            handler_kwargs = {'exc_info': record.exc_info}

        data['level'] = record.levelno
        data['logger'] = record.name

        kwargs['tags'] = tags = {}
        if self.tags:
            tags.update(self.tags)
        tags.update(getattr(record, 'tags', {}))

        kwargs.update(handler_kwargs)
        sample_rate = extra.pop('sample_rate', None)

        return self.client.capture(
            event_type, stack=stack, data=data,
            extra=extra, date=date, sample_rate=sample_rate,
            **kwargs)
