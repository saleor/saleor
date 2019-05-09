import sys

PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
    from urllib2 import build_opener, ProxyHandler, Request, urlopen
    from urllib import urlencode
else:
    from urllib.request import build_opener, ProxyHandler, Request, urlopen
    from urllib.parse import urlencode
    text_type = str


def want_bytes(s, encoding='utf-8', errors='strict'):
    if isinstance(s, text_type):
        s = s.encode(encoding, errors)
    return s
