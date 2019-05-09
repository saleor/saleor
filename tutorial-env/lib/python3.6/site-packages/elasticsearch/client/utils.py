from __future__ import unicode_literals

import weakref
from datetime import date, datetime
from functools import wraps
from ..compat import string_types, quote_plus, PY2

# parts of URL to be omitted
SKIP_IN_PATH = (None, '', b'', [], ())

def _escape(value):
    """
    Escape a single value of a URL string or a query parameter. If it is a list
    or tuple, turn it into a comma-separated string first.
    """

    # make sequences into comma-separated stings
    if isinstance(value, (list, tuple)):
        value = ','.join(value)

    # dates and datetimes into isoformat
    elif isinstance(value, (date, datetime)):
        value = value.isoformat()

    # make bools into true/false strings
    elif isinstance(value, bool):
        value = str(value).lower()

    # don't decode bytestrings
    elif isinstance(value, bytes):
        return value

    # encode strings to utf-8
    if isinstance(value, string_types):
        if PY2 and isinstance(value, unicode):
            return value.encode('utf-8')
        if not PY2 and isinstance(value, str):
            return value.encode('utf-8')

    return str(value)

def _make_path(*parts):
    """
    Create a URL string from parts, omit all `None` values and empty strings.
    Convert lists nad tuples to comma separated values.
    """
    #TODO: maybe only allow some parts to be lists/tuples ?
    return '/' + '/'.join(
        # preserve ',' and '*' in url for nicer URLs in logs
        quote_plus(_escape(p), b',*') for p in parts if p not in SKIP_IN_PATH)

# parameters that apply to all methods
GLOBAL_PARAMS = ('pretty', 'human', 'error_trace', 'format', 'filter_path')

def query_params(*es_query_params):
    """
    Decorator that pops all accepted parameters from method's kwargs and puts
    them in the params argument.
    """
    def _wrapper(func):
        @wraps(func)
        def _wrapped(*args, **kwargs):
            params = {}
            if 'params' in kwargs:
                params = kwargs.pop('params').copy()
            for p in es_query_params + GLOBAL_PARAMS:
                if p in kwargs:
                    v = kwargs.pop(p)
                    if v is not None:
                        params[p] = _escape(v)

            # don't treat ignore and request_timeout as other params to avoid escaping
            for p in ('ignore', 'request_timeout'):
                if p in kwargs:
                    params[p] = kwargs.pop(p)
            return func(*args, params=params, **kwargs)
        return _wrapped
    return _wrapper


class NamespacedClient(object):
    def __init__(self, client):
        self.client = client

    @property
    def transport(self):
        return self.client.transport

class AddonClient(NamespacedClient):
    @classmethod
    def infect_client(cls, client):
        addon = cls(weakref.proxy(client))
        setattr(client, cls.namespace, addon)
        return client
