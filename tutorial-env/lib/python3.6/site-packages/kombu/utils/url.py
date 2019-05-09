"""URL Utilities."""
# flake8: noqa

from __future__ import absolute_import, unicode_literals

try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

from functools import partial

try:
    from urllib.parse import parse_qsl, quote, unquote, urlparse
except ImportError:
    from urllib import quote, unquote                  # noqa
    from urlparse import urlparse, parse_qsl    # noqa
try:
    import ssl
    ssl_available = True
except ImportError:  # pragma: no cover
    ssl_available = False

from kombu.five import bytes_if_py2, string_t

from .compat import NamedTuple
from ..log import get_logger

safequote = partial(quote, safe=bytes_if_py2(''))
logger = get_logger(__name__)


urlparts = NamedTuple('urlparts', [
    ('scheme', str),
    ('hostname', str),
    ('port', int),
    ('username', str),
    ('password', str),
    ('path', str),
    ('query', Mapping),
])


def parse_url(url):
    # type: (str) -> Dict
    """Parse URL into mapping of components."""
    scheme, host, port, user, password, path, query = _parse_url(url)
    if query:
        keys = [key for key in query.keys() if key.startswith('ssl_')]
        for key in keys:
            if key == 'ssl_cert_reqs':
                if ssl_available:
                    query[key] = getattr(ssl, query[key])
                else:
                    query[key] = None
                    logger.warning('Defaulting to insecure SSL behaviour.')

            if 'ssl' not in query:
                query['ssl'] = {}

            query['ssl'][key] = query[key]
            del query[key]

    return dict(transport=scheme, hostname=host,
                port=port, userid=user,
                password=password, virtual_host=path, **query)


def url_to_parts(url):
    # type: (str) -> urlparts
    """Parse URL into :class:`urlparts` tuple of components."""
    scheme = urlparse(url).scheme
    schemeless = url[len(scheme) + 3:]
    # parse with HTTP URL semantics
    parts = urlparse('http://' + schemeless)
    path = parts.path or ''
    path = path[1:] if path and path[0] == '/' else path
    return urlparts(
        scheme,
        unquote(parts.hostname or '') or None,
        parts.port,
        unquote(parts.username or '') or None,
        unquote(parts.password or '') or None,
        unquote(path or '') or None,
        dict(parse_qsl(parts.query)),
    )
_parse_url = url_to_parts  # noqa


def as_url(scheme, host=None, port=None, user=None, password=None,
           path=None, query=None, sanitize=False, mask='**'):
    # type: (str, str, int, str, str, str, str, bool, str) -> str
    """Generate URL from component parts."""
    parts = ['{0}://'.format(scheme)]
    if user or password:
        if user:
            parts.append(safequote(user))
        if password:
            if sanitize:
                parts.extend([':', mask] if mask else [':'])
            else:
                parts.extend([':', safequote(password)])
        parts.append('@')
    parts.append(safequote(host) if host else '')
    if port:
        parts.extend([':', port])
    parts.extend(['/', path])
    return ''.join(str(part) for part in parts if part)


def sanitize_url(url, mask='**'):
    # type: (str, str) -> str
    """Return copy of URL with password removed."""
    return as_url(*_parse_url(url), sanitize=True, mask=mask)


def maybe_sanitize_url(url, mask='**'):
    # type: (Any, str) -> Any
    """Sanitize url, or do nothing if url undefined."""
    if isinstance(url, string_t) and '://' in url:
        return sanitize_url(url, mask)
    return url
