import re

from openid import codecutil  # registers 'oid_percent_escape' encoding handler

# from appendix B of rfc 3986 (http://www.ietf.org/rfc/rfc3986.txt)
uri_pattern = r'^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?'
uri_re = re.compile(uri_pattern)

# gen-delims  = ":" / "/" / "?" / "#" / "[" / "]" / "@"
#
# sub-delims  = "!" / "$" / "&" / "'" / "(" / ")"
#                  / "*" / "+" / "," / ";" / "="
#
# unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"

uri_illegal_char_re = re.compile("[^-A-Za-z0-9:/?#[\]@!$&'()*+,;=._~%]",
                                 re.UNICODE)

authority_pattern = r'^([^@]*@)?([^:]*)(:.*)?'
authority_re = re.compile(authority_pattern)

pct_encoded_pattern = r'%([0-9A-Fa-f]{2})'
pct_encoded_re = re.compile(pct_encoded_pattern)

_unreserved = [False] * 256
for _ in range(ord('A'), ord('Z') + 1):
    _unreserved[_] = True
for _ in range(ord('0'), ord('9') + 1):
    _unreserved[_] = True
for _ in range(ord('a'), ord('z') + 1):
    _unreserved[_] = True
_unreserved[ord('-')] = True
_unreserved[ord('.')] = True
_unreserved[ord('_')] = True
_unreserved[ord('~')] = True


def _pct_encoded_replace_unreserved(mo):
    try:
        i = int(mo.group(1), 16)
        if _unreserved[i]:
            return chr(i)
        else:
            return mo.group().upper()

    except ValueError:
        return mo.group()


def _pct_encoded_replace(mo):
    try:
        return chr(int(mo.group(1), 16))
    except ValueError:
        return mo.group()


def remove_dot_segments(path):
    result_segments = []

    while path:
        if path.startswith('../'):
            path = path[3:]
        elif path.startswith('./'):
            path = path[2:]
        elif path.startswith('/./'):
            path = path[2:]
        elif path == '/.':
            path = '/'
        elif path.startswith('/../'):
            path = path[3:]
            if result_segments:
                result_segments.pop()
        elif path == '/..':
            path = '/'
            if result_segments:
                result_segments.pop()
        elif path == '..' or path == '.':
            path = ''
        else:
            i = 0
            if path[0] == '/':
                i = 1
            i = path.find('/', i)
            if i == -1:
                i = len(path)
            result_segments.append(path[:i])
            path = path[i:]

    return ''.join(result_segments)


def urinorm(uri):
    '''
    Normalize a URI
    '''
    # TODO: use urllib.parse instead of these complex regular expressions
    if isinstance(uri, bytes):
        uri = str(uri, encoding='utf-8')

    uri = uri.encode('ascii', errors='oid_percent_escape').decode('utf-8')
    # _escapeme_re.sub(_pct_escape_unicode, uri).encode('ascii').decode()

    illegal_mo = uri_illegal_char_re.search(uri)
    if illegal_mo:
        raise ValueError('Illegal characters in URI: %r at position %s' %
                         (illegal_mo.group(), illegal_mo.start()))

    uri_mo = uri_re.match(uri)

    scheme = uri_mo.group(2)
    if scheme is None:
        raise ValueError('No scheme specified')

    scheme = scheme.lower()
    if scheme not in ('http', 'https'):
        raise ValueError('Not an absolute HTTP or HTTPS URI: %r' % (uri, ))

    authority = uri_mo.group(4)
    if authority is None:
        raise ValueError('Not an absolute URI: %r' % (uri, ))

    authority_mo = authority_re.match(authority)
    if authority_mo is None:
        raise ValueError('URI does not have a valid authority: %r' % (uri, ))

    userinfo, host, port = authority_mo.groups()

    if userinfo is None:
        userinfo = ''

    if '%' in host:
        host = host.lower()
        host = pct_encoded_re.sub(_pct_encoded_replace, host)
        host = host.encode('idna').decode()
    else:
        host = host.lower()

    if port:
        if (port == ':' or (scheme == 'http' and port == ':80') or
            (scheme == 'https' and port == ':443')):
            port = ''
    else:
        port = ''

    authority = userinfo + host + port

    path = uri_mo.group(5)
    path = pct_encoded_re.sub(_pct_encoded_replace_unreserved, path)
    path = remove_dot_segments(path)
    if not path:
        path = '/'

    query = uri_mo.group(6)
    if query is None:
        query = ''

    fragment = uri_mo.group(8)
    if fragment is None:
        fragment = ''

    return scheme + '://' + authority + path + query + fragment
