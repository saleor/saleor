"""
raven.utils.compat
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2016 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.

Utilities for writing code that runs on Python 2 and 3
"""
# flake8: noqa

# Copyright (c) 2010-2013 Benjamin Peterson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
from __future__ import absolute_import

import operator
import sys
import types


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str


try:
    advance_iterator = next
except NameError:
    def advance_iterator(it):
        return it.next()
next = advance_iterator


try:
    callable = callable
except NameError:
    def callable(obj):
        return any("__call__" in klass.__dict__ for klass in type(obj).__mro__)

if PY3:
    Iterator = object
else:
    class Iterator(object):

        def next(self):
            return type(self).__next__(self)


if PY3:
    def iterkeys(d, **kw):
        return iter(d.keys(**kw))

    def itervalues(d, **kw):
        return iter(d.values(**kw))

    def iteritems(d, **kw):
        return iter(d.items(**kw))

    def iterlists(d, **kw):
        return iter(d.lists(**kw))
else:
    def iterkeys(d, **kw):
        return d.iterkeys(**kw)

    def itervalues(d, **kw):
        return d.itervalues(**kw)

    def iteritems(d, **kw):
        return d.iteritems(**kw)

    def iterlists(d, **kw):
        return d.iterlists(**kw)


if PY3:
    def b(s):
        return s.encode("latin-1")

    def u(s):
        return s
    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO
else:
    def b(s):
        return s
    # Workaround for standalone backslash

    def u(s):
        return unicode(s.replace(r'\\', r'\\\\'), "unicode_escape")
    import StringIO
    StringIO = BytesIO = StringIO.StringIO


if PY3:
    exec_ = getattr(__import__('builtins'), 'exec')

    def reraise(tp, value, tb=None):
        try:
            if value is None:
                value = tp()
            if value.__traceback__ is not tb:
                raise value.with_traceback(tb)
            raise value
        finally:
            value = None
            tb = None

else:
    def exec_(_code_, _globs_=None, _locs_=None):
        """Execute code in a namespace."""
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")

    exec_("""def reraise(tp, value, tb=None):
    try:
        raise tp, value, tb
    finally:
        tb = None
""")


if sys.version_info[:2] == (3, 2):
    exec_("""def raise_from(value, from_value):
    try:
        if from_value is None:
            raise value
        raise value from from_value
    finally:
        value = None
""")
elif sys.version_info[:2] > (3, 2):
    exec_("""def raise_from(value, from_value):
    try:
        raise value from from_value
    finally:
        value = None
""")
else:
    def raise_from(value, from_value):
        raise value


if PY3:
    from urllib.error import HTTPError
    from http import client as httplib
    import urllib.request as urllib2
    from queue import Queue
    from urllib.parse import quote as urllib_quote
    from urllib import parse as urlparse
else:
    from urllib2 import HTTPError
    import httplib
    import urllib2
    from Queue import Queue
    from urllib import quote as urllib_quote
    import urlparse


def get_code(func):
    rv = getattr(func, '__code__', getattr(func, 'func_code', None))
    if rv is None:
        raise TypeError('Could not get code from %r' % type(func).__name__)
    return rv


def check_threads():
    try:
        from uwsgi import opt
    except ImportError:
        return

    # When `threads` is passed in as a uwsgi option,
    # `enable-threads` is implied on.
    if 'threads' in opt:
        return

    if str(opt.get('enable-threads', '0')).lower() in ('false', 'off', 'no', '0'):
        from warnings import warn
        warn(Warning('We detected the use of uwsgi with disabled threads.  '
                     'This will cause issues with the transport you are '
                     'trying to use.  Please enable threading for uwsgi.  '
                     '(Enable the "enable-threads" flag).'))
