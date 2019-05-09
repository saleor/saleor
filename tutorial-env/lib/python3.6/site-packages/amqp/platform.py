"""Platform compatibility."""
from __future__ import absolute_import, unicode_literals

import platform
import re
import struct
import sys

# Jython does not have this attribute
try:
    from socket import SOL_TCP
except ImportError:  # pragma: no cover
    from socket import IPPROTO_TCP as SOL_TCP  # noqa


RE_NUM = re.compile(r'(\d+).+')


def _linux_version_to_tuple(s):
    # type: (str) -> Tuple[int, int, int]
    return tuple(map(_versionatom, s.split('.')[:3]))


def _versionatom(s):
    # type: (str) -> int
    if s.isdigit():
        return int(s)
    match = RE_NUM.match(s)
    return int(match.groups()[0]) if match else 0


# available socket options for TCP level
KNOWN_TCP_OPTS = {
    'TCP_CORK', 'TCP_DEFER_ACCEPT', 'TCP_KEEPCNT',
    'TCP_KEEPIDLE', 'TCP_KEEPINTVL', 'TCP_LINGER2',
    'TCP_MAXSEG', 'TCP_NODELAY', 'TCP_QUICKACK',
    'TCP_SYNCNT', 'TCP_USER_TIMEOUT', 'TCP_WINDOW_CLAMP',
}

LINUX_VERSION = None
if sys.platform.startswith('linux'):
    LINUX_VERSION = _linux_version_to_tuple(platform.release())
    if LINUX_VERSION < (2, 6, 37):
        KNOWN_TCP_OPTS.remove('TCP_USER_TIMEOUT')

    # Windows Subsystem for Linux is an edge-case: the Python socket library
    # returns most TCP_* enums, but they aren't actually supported
    if platform.release().endswith("Microsoft"):
        KNOWN_TCP_OPTS = {'TCP_NODELAY', 'TCP_KEEPIDLE', 'TCP_KEEPINTVL',
                          'TCP_KEEPCNT'}
elif sys.platform.startswith('darwin'):
    KNOWN_TCP_OPTS.remove('TCP_USER_TIMEOUT')

elif 'bsd' in sys.platform:
    KNOWN_TCP_OPTS.remove('TCP_USER_TIMEOUT')

# According to MSDN Windows platforms support getsockopt(TCP_MAXSSEG) but not
# setsockopt(TCP_MAXSEG) on IPPROTO_TCP sockets.
elif sys.platform.startswith('win'):
    KNOWN_TCP_OPTS = {'TCP_NODELAY'}

elif sys.platform.startswith('cygwin'):
    KNOWN_TCP_OPTS = {'TCP_NODELAY'}

if sys.version_info < (2, 7, 7):  # pragma: no cover
    import functools

    def _to_bytes_arg(fun):
        @functools.wraps(fun)
        def _inner(s, *args, **kwargs):
            return fun(s.encode(), *args, **kwargs)
        return _inner

    pack = _to_bytes_arg(struct.pack)
    pack_into = _to_bytes_arg(struct.pack_into)
    unpack = _to_bytes_arg(struct.unpack)
    unpack_from = _to_bytes_arg(struct.unpack_from)
else:
    pack = struct.pack
    pack_into = struct.pack_into
    unpack = struct.unpack
    unpack_from = struct.unpack_from

__all__ = [
    'LINUX_VERSION',
    'SOL_TCP',
    'KNOWN_TCP_OPTS',
    'pack',
    'pack_into',
    'unpack',
    'unpack_from',
]
