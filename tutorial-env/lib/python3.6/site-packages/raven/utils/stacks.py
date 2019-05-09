"""
raven.utils.stacks
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, division

import inspect
import linecache
import re
import os
import sys

from raven.utils.serializer import transform
from raven.utils.compat import iteritems


_coding_re = re.compile(r'coding[:=]\s*([-\w.]+)')


def get_lines_from_file(filename, lineno, context_lines,
                        loader=None, module_name=None):
    """
    Returns context_lines before and after lineno from file.
    Returns (pre_context_lineno, pre_context, context_line, post_context).
    """
    source = None
    if loader is not None and hasattr(loader, "get_source"):
        try:
            source = loader.get_source(module_name)
        except (ImportError, IOError):
            # Traceback (most recent call last):
            #   File "/Users/dcramer/Development/django-sentry/sentry/client/handlers.py", line 31, in emit
            #     get_client().create_from_record(record, request=request)
            #   File "/Users/dcramer/Development/django-sentry/sentry/client/base.py", line 325, in create_from_record
            #     data['__sentry__']['frames'] = varmap(shorten, get_stack_info(stack))
            #   File "/Users/dcramer/Development/django-sentry/sentry/utils/stacks.py", line 112, in get_stack_info
            #     pre_context_lineno, pre_context, context_line, post_context = get_lines_from_file(filename, lineno, 7, loader, module_name)
            #   File "/Users/dcramer/Development/django-sentry/sentry/utils/stacks.py", line 24, in get_lines_from_file
            #     source = loader.get_source(module_name)
            #   File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/pkgutil.py", line 287, in get_source
            #     fullname = self._fix_name(fullname)
            #   File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/pkgutil.py", line 262, in _fix_name
            #     "module %s" % (self.fullname, fullname))
            # ImportError: Loader for module cProfile cannot handle module __main__
            source = None
        if source is not None:
            source = source.splitlines()

    if source is None:
        try:
            source = linecache.getlines(filename)
        except (OSError, IOError):
            return None, None, None

    if not source:
        return None, None, None

    lower_bound = max(0, lineno - context_lines)
    upper_bound = min(lineno + 1 + context_lines, len(source))

    try:
        pre_context = [
            line.strip('\r\n')
            for line in source[lower_bound:lineno]
        ]
        context_line = source[lineno].strip('\r\n')
        post_context = [
            line.strip('\r\n')
            for line in source[(lineno + 1):upper_bound]
        ]
    except IndexError:
        # the file may have changed since it was loaded into memory
        return None, None, None

    return (
        slim_string(pre_context),
        slim_string(context_line),
        slim_string(post_context)
    )


def _getitem_from_frame(f_locals, key, default=None):
    """
    f_locals is not guaranteed to have .get(), but it will always
    support __getitem__. Even if it doesn't, we return ``default``.
    """
    try:
        return f_locals[key]
    except Exception:
        return default


def to_dict(dictish):
    """
    Given something that closely resembles a dictionary, we attempt
    to coerce it into a propery dictionary.
    """
    if hasattr(dictish, 'iterkeys'):
        m = dictish.iterkeys
    elif hasattr(dictish, 'keys'):
        m = dictish.keys
    else:
        raise ValueError(dictish)

    return dict((k, dictish[k]) for k in m())


def iter_traceback_frames(tb):
    """
    Given a traceback object, it will iterate over all
    frames that do not contain the ``__traceback_hide__``
    local variable.
    """
    # Some versions of celery have hacked traceback objects that might
    # miss tb_frame.
    while tb and hasattr(tb, 'tb_frame'):
        # support for __traceback_hide__ which is used by a few libraries
        # to hide internal frames.
        f_locals = getattr(tb.tb_frame, 'f_locals', {})
        if not _getitem_from_frame(f_locals, '__traceback_hide__'):
            yield tb.tb_frame, getattr(tb, 'tb_lineno', None)
        tb = tb.tb_next


def iter_stack_frames(frames=None):
    """
    Given an optional list of frames (defaults to current stack),
    iterates over all frames that do not contain the ``__traceback_hide__``
    local variable.
    """
    if not frames:
        frames = inspect.stack()[1:]

    for frame, lineno in ((f[0], f[2]) for f in frames):
        f_locals = getattr(frame, 'f_locals', {})
        if not _getitem_from_frame(f_locals, '__traceback_hide__'):
            yield frame, lineno


def get_frame_locals(frame, transformer=transform, max_var_size=4096):
    f_locals = getattr(frame, 'f_locals', None)
    if not f_locals:
        return None

    if not isinstance(f_locals, dict):
        # XXX: Genshi (and maybe others) have broken implementations of
        # f_locals that are not actually dictionaries
        try:
            f_locals = to_dict(f_locals)
        except Exception:
            return None

    f_vars = {}
    f_size = 0
    for k, v in iteritems(f_locals):
        v = transformer(v)
        v_size = len(repr(v))
        if v_size + f_size < max_var_size:
            f_vars[k] = v
            f_size += v_size
    return f_vars


def slim_frame_data(frames, frame_allowance=25):
    """
    Removes various excess metadata from middle frames which go beyond
    ``frame_allowance``.

    Returns ``frames``.
    """
    frames_len = 0
    app_frames = []
    system_frames = []
    for frame in frames:
        frames_len += 1
        if frame.get('in_app'):
            app_frames.append(frame)
        else:
            system_frames.append(frame)

    if frames_len <= frame_allowance:
        return frames

    remaining = frames_len - frame_allowance
    app_count = len(app_frames)
    system_allowance = max(frame_allowance - app_count, 0)
    if system_allowance:
        half_max = int(system_allowance / 2)
        # prioritize trimming system frames
        for frame in system_frames[half_max:-half_max]:
            frame.pop('vars', None)
            frame.pop('pre_context', None)
            frame.pop('post_context', None)
            remaining -= 1

    else:
        for frame in system_frames:
            frame.pop('vars', None)
            frame.pop('pre_context', None)
            frame.pop('post_context', None)
            remaining -= 1

    if remaining:
        app_allowance = app_count - remaining
        half_max = int(app_allowance / 2)

        for frame in app_frames[half_max:-half_max]:
            frame.pop('vars', None)
            frame.pop('pre_context', None)
            frame.pop('post_context', None)

    return frames


def slim_string(value, length=512):
    if not value:
        return value
    if len(value) > length:
        return value[:length - 3] + '...'
    return value[:length]


def get_stack_info(frames, transformer=transform, capture_locals=True,
                   frame_allowance=25):
    """
    Given a list of frames, returns a list of stack information
    dictionary objects that are JSON-ready.

    We have to be careful here as certain implementations of the
    _Frame class do not contain the necessary data to lookup all
    of the information we want.
    """
    __traceback_hide__ = True  # NOQA

    result = []
    for frame_info in frames:
        # Old, terrible API
        if isinstance(frame_info, (list, tuple)):
            frame, lineno = frame_info

        else:
            frame = frame_info
            lineno = frame_info.f_lineno

        # Support hidden frames
        f_locals = getattr(frame, 'f_locals', {})
        if _getitem_from_frame(f_locals, '__traceback_hide__'):
            continue

        f_globals = getattr(frame, 'f_globals', {})

        f_code = getattr(frame, 'f_code', None)
        if f_code:
            abs_path = frame.f_code.co_filename
            function = frame.f_code.co_name
        else:
            abs_path = None
            function = None

        loader = _getitem_from_frame(f_globals, '__loader__')
        module_name = _getitem_from_frame(f_globals, '__name__')

        if lineno:
            lineno -= 1

        if lineno is not None and abs_path:
            pre_context, context_line, post_context = \
                get_lines_from_file(abs_path, lineno, 5, loader, module_name)
        else:
            pre_context, context_line, post_context = None, None, None

        # Try to pull a relative file path
        # This changes /foo/site-packages/baz/bar.py into baz/bar.py
        try:
            base_filename = sys.modules[module_name.split('.', 1)[0]].__file__
            filename = abs_path.split(
                base_filename.rsplit(os.sep, 2)[0], 1)[-1].lstrip(os.sep)
        except Exception:
            filename = abs_path

        if not filename:
            filename = abs_path

        frame_result = {
            'abs_path': abs_path,
            'filename': filename,
            'module': module_name or None,
            'function': function or '<unknown>',
            'lineno': lineno + 1,
        }
        if capture_locals:
            f_vars = get_frame_locals(frame, transformer=transformer)
            if f_vars:
                frame_result['vars'] = f_vars

        if context_line is not None:
            frame_result.update({
                'pre_context': pre_context,
                'context_line': context_line,
                'post_context': post_context,
            })
        result.append(frame_result)

    stackinfo = {
        'frames': slim_frame_data(result, frame_allowance=frame_allowance),
    }

    return stackinfo
