"""Promises, promises, promises."""
from __future__ import absolute_import, unicode_literals

import re

from collections import namedtuple

from .abstract import Thenable
from .promises import promise
from .synchronization import barrier
from .funtools import (
    maybe_promise, ensure_promise,
    ppartial, preplace, starpromise, transform, wrap,
)


__version__ = '1.3.0'
__author__ = 'Ask Solem'
__contact__ = 'ask@celeryproject.org'
__homepage__ = 'http://github.com/celery/vine'
__docformat__ = 'restructuredtext'

# -eof meta-

version_info_t = namedtuple('version_info_t', (
    'major', 'minor', 'micro', 'releaselevel', 'serial',
))
# bump version can only search for {current_version}
# so we have to parse the version here.
_temp = re.match(
    r'(\d+)\.(\d+).(\d+)(.+)?', __version__).groups()
VERSION = version_info = version_info_t(
    int(_temp[0]), int(_temp[1]), int(_temp[2]), _temp[3] or '', '')
del(_temp)
del(re)

__all__ = [
    'Thenable', 'promise', 'barrier',
    'maybe_promise', 'ensure_promise',
    'ppartial', 'preplace', 'starpromise', 'transform', 'wrap',
]
