# -*- coding: utf-8 -*-
"""JSON Serialization Utilities."""
from __future__ import absolute_import, unicode_literals

import datetime
import decimal
import json as stdjson
import uuid

from kombu.five import PY3, buffer_t, text_t, bytes_t

try:
    from django.utils.functional import Promise as DjangoPromise
except ImportError:  # pragma: no cover
    class DjangoPromise(object):  # noqa
        """Dummy object."""

try:
    import simplejson as json
    from simplejson.decoder import JSONDecodeError as _DecodeError
    _json_extra_kwargs = {'use_decimal': False}
except ImportError:                 # pragma: no cover
    import json                     # noqa
    _json_extra_kwargs = {}           # noqa

    class _DecodeError(Exception):  # noqa
        pass


_encoder_cls = type(json._default_encoder)
_default_encoder = None   # ... set to JSONEncoder below.


class JSONEncoder(_encoder_cls):
    """Kombu custom json encoder."""

    def default(self, o,
                dates=(datetime.datetime, datetime.date),
                times=(datetime.time,),
                textual=(decimal.Decimal, uuid.UUID, DjangoPromise),
                isinstance=isinstance,
                datetime=datetime.datetime,
                text_t=text_t):
        reducer = getattr(o, '__json__', None)
        if reducer is not None:
            return reducer()
        else:
            if isinstance(o, dates):
                if not isinstance(o, datetime):
                    o = datetime(o.year, o.month, o.day, 0, 0, 0, 0)
                r = o.isoformat()
                if r.endswith("+00:00"):
                    r = r[:-6] + "Z"
                return r
            elif isinstance(o, times):
                return o.isoformat()
            elif isinstance(o, textual):
                return text_t(o)
            return super(JSONEncoder, self).default(o)


_default_encoder = JSONEncoder


def dumps(s, _dumps=json.dumps, cls=None,
          default_kwargs=_json_extra_kwargs, **kwargs):
    """Serialize object to json string."""
    return _dumps(s, cls=cls or _default_encoder,
                  **dict(default_kwargs, **kwargs))


def loads(s, _loads=json.loads, decode_bytes=PY3):
    """Deserialize json from string."""
    # None of the json implementations supports decoding from
    # a buffer/memoryview, or even reading from a stream
    #    (load is just loads(fp.read()))
    # but this is Python, we love copying strings, preferably many times
    # over.  Note that pickle does support buffer/memoryview
    # </rant>
    if isinstance(s, memoryview):
        s = s.tobytes().decode('utf-8')
    elif isinstance(s, bytearray):
        s = s.decode('utf-8')
    elif decode_bytes and isinstance(s, bytes_t):
        s = s.decode('utf-8')
    elif isinstance(s, buffer_t):
        s = text_t(s)  # ... awwwwwww :(

    try:
        return _loads(s)
    except _DecodeError:
        # catch "Unpaired high surrogate" error
        return stdjson.loads(s)
