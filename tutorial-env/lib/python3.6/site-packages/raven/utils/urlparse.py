from __future__ import absolute_import

# Can't use the compat module here because of an import loop
try:
    import urlparse as _urlparse
except ImportError:
    from urllib import parse as _urlparse


def register_scheme(scheme):
    for method in filter(lambda s: s.startswith('uses_'), dir(_urlparse)):
        uses = getattr(_urlparse, method)
        if scheme not in uses:
            uses.append(scheme)


urlparse = _urlparse.urlparse
parse_qsl = _urlparse.parse_qsl
