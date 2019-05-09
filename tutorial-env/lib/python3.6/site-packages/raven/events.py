"""
raven.events
~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.

"""
from __future__ import absolute_import

import logging
import sys

from raven.utils.encoding import to_unicode
from raven.utils.stacks import get_stack_info, iter_traceback_frames

__all__ = ('BaseEvent', 'Exception', 'Message', 'Query')


class BaseEvent(object):
    def __init__(self, client):
        self.client = client
        self.logger = logging.getLogger(__name__)

    def to_string(self, data):
        raise NotImplementedError

    def capture(self, **kwargs):
        return {
        }

    def transform(self, value):
        return self.client.transform(value)


# The __suppress_context__ attribute was added in Python 3.3.
# See PEP 415 for details:
# https://www.python.org/dev/peps/pep-0415/
if hasattr(Exception, '__suppress_context__'):
    def _chained_exceptions(exc_info):
        """
        Return a generator iterator over an exception's chain.

        The exceptions are yielded from outermost to innermost (i.e. last to
        first when viewing a stack trace).

        """
        yield exc_info
        exc_type, exc, exc_traceback = exc_info

        context = set()
        context.add(exc)
        while True:
            if exc.__suppress_context__:
                # Then __cause__ should be used instead.
                exc = exc.__cause__
            else:
                exc = exc.__context__
            if exc in context:
                break
            context.add(exc)
            if exc is None:
                break
            yield type(exc), exc, exc.__traceback__
else:
    # Then we do not support reporting exception chains.
    def _chained_exceptions(exc_info):
        yield exc_info


class Exception(BaseEvent):
    """
    Exceptions store the following metadata:

    - value: 'My exception value'
    - type: 'ClassName'
    - module '__builtin__' (i.e. __builtin__.TypeError)
    - frames: a list of serialized frames (see _get_traceback_frames)

    """

    name = 'exception'

    def to_string(self, data):
        exc = data[self.name]['values'][-1]
        if exc['value']:
            return '%s: %s' % (exc['type'], exc['value'])
        return exc['type']

    def _get_value(self, exc_type, exc_value, exc_traceback):
        """
        Convert exception info to a value for the values list.
        """
        stack_info = get_stack_info(
            iter_traceback_frames(exc_traceback),
            transformer=self.transform,
            capture_locals=self.client.capture_locals,
        )

        exc_module = getattr(exc_type, '__module__', None)
        if exc_module:
            exc_module = str(exc_module)
        exc_type = getattr(exc_type, '__name__', '<unknown>')

        return {
            'value': to_unicode(exc_value),
            'type': str(exc_type),
            'module': to_unicode(exc_module),
            'stacktrace': stack_info,
        }

    def capture(self, exc_info=None, **kwargs):
        if not exc_info or exc_info is True:
            exc_info = sys.exc_info()

        if not exc_info:
            raise ValueError('No exception found')

        values = []
        for exc_info in _chained_exceptions(exc_info):
            value = self._get_value(*exc_info)
            values.insert(0, value)

        return {
            'level': kwargs.get('level', logging.ERROR),
            self.name: {'values': values},
        }


class Message(BaseEvent):
    """
    Messages store the following metadata:

    - message: 'My message from %s about %s'
    - params: ('foo', 'bar')
    """

    name = 'sentry.interfaces.Message'

    def to_string(self, data):
        return data[self.name]['message']

    def capture(self, message, params=(), formatted=None, **kwargs):
        message = to_unicode(message)
        data = {
            self.name: {
                'message': message,
                'params': self.transform(params),
                'formatted': formatted,
            },
        }
        if 'message' not in data:
            data['message'] = formatted or message
        return data


class Query(BaseEvent):
    """
    Messages store the following metadata:

    - query: 'SELECT * FROM table'
    - engine: 'postgesql_psycopg2'
    """

    name = 'sentry.interfaces.Query'

    def to_string(self, data):
        sql = data[self.name]
        return sql['query']

    def capture(self, query, engine, **kwargs):
        return {
            self.name: {
                'query': to_unicode(query),
                'engine': str(engine),
            }
        }
