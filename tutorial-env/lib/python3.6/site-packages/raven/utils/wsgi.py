"""
This module implements WSGI related helpers adapted from ``werkzeug.wsgi``

:copyright: (c) 2010 by the Werkzeug Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.utils.compat import iteritems, urllib_quote


# `get_headers` comes from `werkzeug.datastructures.EnvironHeaders`
def get_headers(environ):
    """
    Returns only proper HTTP headers.
    """
    for key, value in iteritems(environ):
        key = str(key)
        if key.startswith('HTTP_') and key not in \
           ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
            yield key[5:].replace('_', '-').title(), value
        elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            yield key.replace('_', '-').title(), value


def get_environ(environ):
    """
    Returns our whitelisted environment variables.
    """
    for key in ('REMOTE_ADDR', 'SERVER_NAME', 'SERVER_PORT'):
        if key in environ:
            yield key, environ[key]


# `get_host` comes from `werkzeug.wsgi`
def get_host(environ):
    """Return the real host for the given WSGI environment.  This takes care
    of the `X-Forwarded-Host` header.

    :param environ: the WSGI environment to get the host of.
    """
    scheme = environ.get('wsgi.url_scheme')
    if 'HTTP_X_FORWARDED_HOST' in environ:
        result = environ['HTTP_X_FORWARDED_HOST']
    elif 'HTTP_HOST' in environ:
        result = environ['HTTP_HOST']
    else:
        result = environ['SERVER_NAME']
        if (scheme, str(environ['SERVER_PORT'])) not \
           in (('https', '443'), ('http', '80')):
            result += ':' + environ['SERVER_PORT']
    if result.endswith(':80') and scheme == 'http':
        result = result[:-3]
    elif result.endswith(':443') and scheme == 'https':
        result = result[:-4]
    return result


# `get_current_url` comes from `werkzeug.wsgi`
def get_current_url(environ, root_only=False, strip_querystring=False,
                    host_only=False):
    """A handy helper function that recreates the full URL for the current
    request or parts of it.  Here an example:

    >>> from werkzeug import create_environ
    >>> env = create_environ("/?param=foo", "http://localhost/script")
    >>> get_current_url(env)
    'http://localhost/script/?param=foo'
    >>> get_current_url(env, root_only=True)
    'http://localhost/script/'
    >>> get_current_url(env, host_only=True)
    'http://localhost/'
    >>> get_current_url(env, strip_querystring=True)
    'http://localhost/script/'

    :param environ: the WSGI environment to get the current URL from.
    :param root_only: set `True` if you only want the root URL.
    :param strip_querystring: set to `True` if you don't want the querystring.
    :param host_only: set to `True` if the host URL should be returned.
    """
    tmp = [environ['wsgi.url_scheme'], '://', get_host(environ)]
    cat = tmp.append
    if host_only:
        return ''.join(tmp) + '/'
    cat(urllib_quote(environ.get('SCRIPT_NAME', '').rstrip('/')))
    if root_only:
        cat('/')
    else:
        cat(urllib_quote('/' + environ.get('PATH_INFO', '').lstrip('/')))
        if not strip_querystring:
            qs = environ.get('QUERY_STRING')
            if qs:
                cat('?' + qs)
    return ''.join(tmp)


def get_client_ip(environ):
    """
    Naively yank the first IP address in an X-Forwarded-For header
    and assume this is correct.

    Note: Don't use this in security sensitive situations since this
    value may be forged from a client.
    """
    try:
        return environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    except (KeyError, IndexError):
        return environ.get('REMOTE_ADDR')
