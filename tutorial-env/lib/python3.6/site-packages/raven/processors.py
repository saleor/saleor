"""
raven.core.processors
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import re
import warnings

from raven.utils.compat import string_types, text_type, PY3
from raven.utils import varmap


class Processor(object):
    def __init__(self, client):
        self.client = client

    def get_data(self, data, **kwargs):
        return

    def process(self, data, **kwargs):
        resp = self.get_data(data, **kwargs)
        if resp:
            data = resp

        if 'exception' in data:
            if 'values' in data['exception']:
                for value in data['exception'].get('values', []):
                    if 'stacktrace' in value:
                        self.filter_stacktrace(value['stacktrace'])

        if 'request' in data:
            self.filter_http(data['request'])

        if 'extra' in data:
            data['extra'] = self.filter_extra(data['extra'])

        return data

    def filter_stacktrace(self, data):
        pass

    def filter_http(self, data):
        pass

    def filter_extra(self, data):
        return data


class RemovePostDataProcessor(Processor):
    """Removes HTTP post data."""

    def filter_http(self, data, **kwargs):
        data.pop('data', None)


class RemoveStackLocalsProcessor(Processor):
    """Removes local context variables from stacktraces."""

    def filter_stacktrace(self, data, **kwargs):
        for frame in data.get('frames', []):
            frame.pop('vars', None)


class SanitizeKeysProcessor(Processor):
    """
    Asterisk out things that correspond to a configurable set of keys.
    """

    MASK = '*' * 8

    @property
    def sanitize_keys(self):
        keys = getattr(self.client, 'sanitize_keys')
        if keys is None:
            raise ValueError('The sanitize_keys setting must be present to use SanitizeKeysProcessor')
        return keys

    def sanitize(self, item, value):
        if value is None:
            return

        if not item:  # key can be a NoneType
            return value

        # Just in case we have bytes here, we want to make them into text
        # properly without failing so we can perform our check.
        if isinstance(item, bytes):
            item = item.decode('utf-8', 'replace')
        else:
            item = text_type(item)

        item = item.lower()
        for key in self.sanitize_keys:
            if key in item:
                # store mask as a fixed length for security
                return self.MASK
        return value

    def filter_stacktrace(self, data):
        for frame in data.get('frames', []):
            if 'vars' not in frame:
                continue
            frame['vars'] = varmap(self.sanitize, frame['vars'])

    def filter_http(self, data):
        for n in ('data', 'cookies', 'headers', 'env', 'query_string'):
            if n not in data:
                continue

            # data could be provided as bytes
            if PY3 and isinstance(data[n], bytes):
                data[n] = data[n].decode('utf-8', 'replace')

            if isinstance(data[n], string_types) and '=' in data[n]:
                # at this point we've assumed it's a standard HTTP query
                # or cookie
                if n == 'cookies':
                    delimiter = ';'
                else:
                    delimiter = '&'

                data[n] = self._sanitize_keyvals(data[n], delimiter)
            else:
                data[n] = varmap(self.sanitize, data[n])
                if n == 'headers' and 'Cookie' in data[n]:
                    data[n]['Cookie'] = self._sanitize_keyvals(
                        data[n]['Cookie'], ';'
                    )

    def filter_extra(self, data):
        return varmap(self.sanitize, data)

    def _sanitize_keyvals(self, keyvals, delimiter):
        sanitized_keyvals = []
        for keyval in keyvals.split(delimiter):
            keyval = keyval.split('=')
            if len(keyval) == 2:
                sanitized_keyvals.append((keyval[0], self.sanitize(*keyval)))
            else:
                sanitized_keyvals.append(keyval)

        return delimiter.join('='.join(keyval) for keyval in sanitized_keyvals)


class SanitizePasswordsProcessor(SanitizeKeysProcessor):
    """
    Asterisk out things that look like passwords, credit card numbers,
    and API keys in frames, http, and basic extra data.
    """

    KEYS = frozenset([
        'password',
        'secret',
        'passwd',
        'authorization',
        'api_key',
        'apikey',
        'sentry_dsn',
        'access_token',
    ])
    VALUES_RE = re.compile(r'^(?:\d[ -]*?){13,16}$')

    @property
    def sanitize_keys(self):
        return self.KEYS

    @property
    def FIELDS(self):
        warnings.warn(
            "`SanitizePasswordsProcessor.Fields` has been deprecated. Use "
            "`SanitizePasswordsProcessor.KEYS` or `SanitizePasswordsProcessor.sanitize_keys` "
            "instead",
            DeprecationWarning,
        )
        return self.KEYS

    def sanitize(self, item, value):
        value = super(SanitizePasswordsProcessor, self).sanitize(item, value)
        if isinstance(value, string_types) and self.VALUES_RE.match(value):
            return self.MASK
        return value
