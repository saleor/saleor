"""
raven.contrib.django.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import os
from django.conf import settings


def linebreak_iter(template_source):
    yield 0
    p = template_source.find('\n')
    while p >= 0:
        yield p + 1
        p = template_source.find('\n', p + 1)
    yield len(template_source) + 1


def get_data_from_template(source, debug=None):
    def _remove_numbers(items):
        rv = []
        for item in items:
            # Some debug info from django has tuples in the form (lineno,
            # code) instead of just the code there.
            if isinstance(item, (list, tuple)) and len(item) == 2:
                item = item[1]
            rv.append(item)
        return rv

    if debug is not None:
        lineno = debug['line']
        filename = debug['name']
        source_lines = []
        source_lines += [''] * (debug['source_lines'][0][0])
        for num, line in debug['source_lines']:
            source_lines.append(line)
        source_lines += [''] * 4
    elif source:
        origin, (start, end) = source
        filename = culprit = getattr(origin, 'loadname', None)
        template_source = origin.reload()
        lineno = None
        upto = 0
        source_lines = []
        for num, next in enumerate(linebreak_iter(template_source)):
            if start >= upto and end <= next:
                lineno = num
            source_lines.append(template_source[upto:next])
            upto = next

        if not source_lines or lineno is None:
            return {}
    else:
        raise TypeError('Source or debug needed')

    if filename is None:
        filename = '<unknown filename>'
        culprit = '<unknown filename>'
    else:
        culprit = filename.split('/templates/')[-1]

    pre_context = _remove_numbers(source_lines[max(lineno - 3, 0):lineno])
    post_context = _remove_numbers(source_lines[(lineno + 1):(lineno + 4)])
    context_line = _remove_numbers([source_lines[lineno]])[0]

    return {
        'template': {
            'filename': os.path.basename(filename),
            'abs_path': filename,
            'pre_context': pre_context,
            'context_line': context_line,
            'lineno': lineno,
            'post_context': post_context,
        },
        'culprit': culprit,
    }


def get_host(request):
    """
    A reimplementation of Django's get_host, without the
    SuspiciousOperation check.
    """
    # We try three options, in order of decreasing preference.
    if settings.USE_X_FORWARDED_HOST and (
            'HTTP_X_FORWARDED_HOST' in request.META):
        host = request.META['HTTP_X_FORWARDED_HOST']
    elif 'HTTP_HOST' in request.META:
        host = request.META['HTTP_HOST']
    else:
        # Reconstruct the host using the algorithm from PEP 333.
        host = request.META['SERVER_NAME']
        server_port = str(request.META['SERVER_PORT'])
        if server_port != (request.is_secure() and '443' or '80'):
            host = '%s:%s' % (host, server_port)
    return host
