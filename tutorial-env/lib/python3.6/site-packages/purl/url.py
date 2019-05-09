from __future__ import unicode_literals

try:
    from urllib.parse import parse_qs, urlencode, urlparse, quote, unquote
except ImportError:
    from urllib import urlencode, quote, unquote
    from urlparse import parse_qs, urlparse
from collections import namedtuple

import six


# To minimise memory consumption, we use a namedtuple to store all instance
# variables, as well as using the __slots__ attribute.
_URLTuple = namedtuple(
    "_URLTuple", "host username password scheme port path query fragment")


# Encoding helpers


def to_unicode(string):
    """
    Ensure a passed string is unicode
    """
    if isinstance(string, six.binary_type):
        return string.decode('utf8')
    if isinstance(string, six.text_type):
        return string
    if six.PY2:
        return unicode(string)
    return str(string)


def to_utf8(string):
    """
    Encode a string as a UTF8 bytestring.  This function could be passed a
    bytestring or unicode string so must distinguish between the two.
    """
    if isinstance(string, six.text_type):
        return string.encode('utf8')
    if isinstance(string, six.binary_type):
        return string
    return str(string)


def dict_to_unicode(raw_dict):
    """
    Ensure all keys and values in a dict are unicode.

    The passed dict is assumed to have lists for all values.
    """
    decoded = {}
    for key, value in raw_dict.items():
        decoded[to_unicode(key)] = map(
            to_unicode, value)
    return decoded


def unicode_quote(string, safe='/'):
    if string is None:
        return None
    return quote(to_utf8(string), to_utf8(safe))


def unicode_quote_path_segment(string):
    if string is None:
        return None
    return quote(to_utf8(string), safe=to_utf8(""))


def unicode_unquote(string):
    if string is None:
        return None
    if six.PY3:
        return unquote(string)
    return to_unicode(unquote(to_utf8(string)))


def unicode_urlencode(query, doseq=True):
    """
    Custom wrapper around urlencode to support unicode

    Python urlencode doesn't handle unicode well so we need to convert to
    bytestrings before using it:
    http://stackoverflow.com/questions/6480723/urllib-urlencode-doesnt-like-unicode-values-how-about-this-workaround
    """
    pairs = []
    for key, value in query.items():
        if isinstance(value, list):
            value = list(map(to_utf8, value))
        else:
            value = to_utf8(value)
        pairs.append((to_utf8(key), value))
    encoded_query = dict(pairs)
    xx = urlencode(encoded_query, doseq)
    return xx


def parse(url_str):
    """
    Extract all parts from a URL string and return them as a dictionary
    """
    url_str = to_unicode(url_str)
    result = urlparse(url_str)
    netloc_parts = result.netloc.rsplit('@', 1)
    if len(netloc_parts) == 1:
        username = password = None
        host = netloc_parts[0]
    else:
        user_and_pass = netloc_parts[0].split(':')
        if len(user_and_pass) == 2:
            username, password = user_and_pass
        elif len(user_and_pass) == 1:
            username = user_and_pass[0]
            password = None
        host = netloc_parts[1]

    if host and ':' in host:
        host = host.split(':')[0]

    return {'host': host,
            'username': username,
            'password': password,
            'scheme': result.scheme,
            'port': result.port,
            'path': result.path,
            'query': result.query,
            'fragment': result.fragment}


class URL(object):
    """
    The constructor can be used in two ways:

    1. Pass a URL string::

        >>> URL('http://www.google.com/search?q=testing').as_string()
        'http://www.google.com/search?q=testing'

    2. Pass keyword arguments::

        >>> URL(host='www.google.com', path='/search', query='q=testing').as_string()
        'http://www.google.com/search?q=testing'

    If you pass both a URL string and keyword args, then the values of keyword
    args take precedence.
    """

    __slots__ = ("_tuple",)

    def __init__(self, url_str=None, host=None, username=None, password=None,
                 scheme=None, port=None, path=None, query=None, fragment=None):
        if url_str is not None:
            params = parse(url_str)
        else:
            # Defaults
            params = {'scheme': 'http',
                      'username': None,
                      'password': None,
                      'host': None,
                      'port': None,
                      'path': '/',
                      'query': None,
                      'fragment': None}

        # Ensure path starts with a slash
        if path and not path.startswith("/"):
            path = "/%s" % path

        # Kwargs override the url_str
        for var in 'host username password scheme port path query fragment'.split():
            if locals()[var] is not None:
                params[var] = locals()[var]

        # Store the various components in %-encoded form
        self._tuple = _URLTuple(params['host'],
                                unicode_quote(params['username']),
                                unicode_quote(params['password']),
                                params['scheme'],
                                params['port'],
                                params['path'],
                                params['query'],
                                unicode_quote(params['fragment']))

    def __eq__(self, other):
        return self._tuple == other._tuple

    def __ne__(self, other):
        return self._tuple != other._tuple

    def __getstate__(self):
        return tuple(self._tuple)

    def __setstate__(self, state):
        self._tuple = _URLTuple(*state)

    def __hash__(self):
        return hash(self._tuple)

    def __repr__(self):
        return str(self._tuple)

    def __unicode__(self):
        url = self._tuple
        parts = ["%s://" % url.scheme if url.scheme else '',
                 self.netloc(),
                 url.path,
                 '?%s' % url.query if url.query else '',
                 '#%s' % url.fragment if url.fragment else '']
        if not url.host:
            return ''.join(parts[2:])
        return ''.join(parts)

    __str__ = as_string = __unicode__

    # Accessors / Mutators
    # These use the jQuery overloading style whereby they become mutators if
    # extra args are passed

    def netloc(self):
        """
        Return the netloc
        """
        url = self._tuple
        if url.username and url.password:
            netloc = '%s:%s@%s' % (url.username, url.password, url.host)
        elif url.username and not url.password:
            netloc = '%s@%s' % (url.username, url.host)
        else:
            netloc = url.host
        if url.port:
            netloc = '%s:%s' % (netloc, url.port)
        return netloc

    def host(self, value=None):
        """
        Return the host

        :param string value: new host string
        """
        if value is not None:
            return URL._mutate(self, host=value)
        return self._tuple.host

    domain = host

    def username(self, value=None):
        """
        Return or set the username

        :param string value: the new username to use
        :returns: string or new :class:`URL` instance
        """
        if value is not None:
            return URL._mutate(self, username=value)
        return unicode_unquote(self._tuple.username)

    def password(self, value=None):
        """
        Return or set the password

        :param string value: the new password to use
        :returns: string or new :class:`URL` instance
        """
        if value is not None:
            return URL._mutate(self, password=value)
        return unicode_unquote(self._tuple.password)

    def subdomains(self, value=None):
        """
        Returns a list of subdomains or set the subdomains and returns a
        new :class:`URL` instance.

        :param list value: a list of subdomains
        """
        if value is not None:
            return URL._mutate(self, host='.'.join(value))
        return self.host().split('.')

    def subdomain(self, index, value=None):
        """
        Return a subdomain or set a new value and return a new :class:`URL`
        instance.

        :param integer index: 0-indexed subdomain
        :param string value: New subdomain
        """
        if value is not None:
            subdomains = self.subdomains()
            subdomains[index] = value
            return URL._mutate(self, host='.'.join(subdomains))
        return self.subdomains()[index]

    def scheme(self, value=None):
        """
        Return or set the scheme.

        :param string value: the new scheme to use
        :returns: string or new :class:`URL` instance
        """
        if value is not None:
            return URL._mutate(self, scheme=value)
        return self._tuple.scheme

    def path(self, value=None):
        """
        Return or set the path

        :param string value: the new path to use
        :returns: string or new :class:`URL` instance
        """
        if value is not None:
            if not value.startswith('/'):
                value = '/' + value
            encoded_value = unicode_quote(value)
            return URL._mutate(self, path=encoded_value)
        return self._tuple.path

    def query(self, value=None):
        """
        Return or set the query string

        :param string value: the new query string to use
        :returns: string or new :class:`URL` instance
        """
        if value is not None:
            return URL._mutate(self, query=value)
        return self._tuple.query

    def port(self, value=None):
        """
        Return or set the port

        :param string value: the new port to use
        :returns: string or new :class:`URL` instance
        """
        if value is not None:
            return URL._mutate(self, port=value)
        return self._tuple.port

    def fragment(self, value=None):
        """
        Return or set the fragment (hash)

        :param string value: the new fragment to use
        :returns: string or new :class:`URL` instance
        """
        if value is not None:
            return URL._mutate(self, fragment=value)
        return unicode_unquote(self._tuple.fragment)

    def relative(self):
        """
        Return a relative URL object (eg strip the protocol and host)

        :returns: new :class:`URL` instance
        """
        return URL._mutate(self, scheme=None, host=None)

    # ====
    # Path
    # ====

    def path_segment(self, index, value=None, default=None):
        """
        Return the path segment at the given index

        :param integer index:
        :param string value: the new segment value
        :param string default: the default value to return if no path segment exists with the given index
        """
        if value is not None:
            segments = list(self.path_segments())
            segments[index] = unicode_quote_path_segment(value)
            new_path = '/' + '/'.join(segments)
            if self._tuple.path.endswith('/'):
                new_path += '/'
            return URL._mutate(self, path=new_path)
        try:
            return self.path_segments()[index]
        except IndexError:
            return default

    def path_segments(self, value=None):
        """
        Return the path segments

        :param list value: the new path segments to use
        """
        if value is not None:
            encoded_values = map(unicode_quote_path_segment, value)
            new_path = '/' + '/'.join(encoded_values)
            return URL._mutate(self, path=new_path)
        parts = self._tuple.path.split('/')
        segments = parts[1:]
        if self._tuple.path.endswith('/'):
            segments.pop()
        segments = map(unicode_unquote, segments)
        return tuple(segments)

    def add_path_segment(self, value):
        """
        Add a new path segment to the end of the current string

        :param string value: the new path segment to use

        Example::

            >>> u = URL('http://example.com/foo/')
            >>> u.add_path_segment('bar').as_string()
            'http://example.com/foo/bar'
        """
        segments = self.path_segments() + (to_unicode(value),)
        return self.path_segments(segments)

    # ============
    # Query params
    # ============

    def has_query_param(self, key):
        """
        Test if a given query parameter is present

        :param string key: key to test for
        """
        return self.query_param(key) is not None

    def has_query_params(self, keys):
        """
        Test if a given set of query parameters are present

        :param list keys: keys to test for
        """
        return all([self.has_query_param(k) for k in keys])

    def query_param(self, key, value=None, default=None, as_list=False):
        """
        Return or set a query parameter for the given key

        The value can be a list.

        :param string key: key to look for
        :param string default: value to return if ``key`` isn't found
        :param boolean as_list: whether to return the values as a list
        :param string value: the new query parameter to use
        """
        parse_result = self.query_params()
        if value is not None:
            # Need to ensure all strings are unicode
            if isinstance(value, (list, tuple)):
                value = list(map(to_unicode, value))
            else:
                value = to_unicode(value)
            parse_result[to_unicode(key)] = value
            return URL._mutate(
                self, query=unicode_urlencode(parse_result, doseq=True))

        try:
            result = parse_result[key]
        except KeyError:
            return default
        if as_list:
            return result
        return result[0] if len(result) == 1 else result

    def append_query_param(self, key, value):
        """
        Append a query parameter

        :param string key: The query param key
        :param string value: The new value
        """
        values = self.query_param(key, as_list=True, default=[])
        values.append(value)
        return self.query_param(key, values)

    def query_params(self, value=None):
        """
        Return or set a dictionary of query params

        :param dict value: new dictionary of values
        """
        if value is not None:
            return URL._mutate(self, query=unicode_urlencode(value, doseq=True))
        query = '' if self._tuple.query is None else self._tuple.query

        # In Python 2.6, urlparse needs a bytestring so we encode and then
        # decode the result.
        if not six.PY3:
            result = parse_qs(to_utf8(query), True)
            return dict_to_unicode(result)

        return parse_qs(query, True)

    def remove_query_param(self, key, value=None):
        """
        Remove a query param from a URL

        Set the value parameter if removing from a list.

        :param string key: The key to delete
        :param string value: The value of the param to delete (of more than one)
        """
        parse_result = self.query_params()
        if value is not None:
            index = parse_result[key].index(value)
            del parse_result[key][index]
        else:
            del parse_result[key]
        return URL._mutate(self, query=unicode_urlencode(parse_result, doseq=True))

    # =======
    # Helpers
    # =======

    @classmethod
    def _mutate(cls, url, **kwargs):
        args = url._tuple._asdict()
        args.update(kwargs)
        return cls(**args)

    @classmethod
    def from_string(cls, url_str):
        """
        Factory method to create a new instance based on a passed string

        This method is deprecated now
        """
        return cls(url_str)
