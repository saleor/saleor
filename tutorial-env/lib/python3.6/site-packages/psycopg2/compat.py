import sys

__all__ = ['string_types', 'text_type', 'lru_cache']

if sys.version_info[0] == 2:
    # Python 2
    PY2 = True
    PY3 = False
    string_types = basestring,
    text_type = unicode
    from ._lru_cache import lru_cache

else:
    # Python 3
    PY2 = False
    PY3 = True
    string_types = str,
    text_type = str
    from functools import lru_cache
