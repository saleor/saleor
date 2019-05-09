"""
raven.contrib.webpy.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import web

from raven.utils.wsgi import get_headers, get_environ


def get_data_from_request():
    """Returns request data extracted from web.ctx."""
    return {
        'request': {
            'url': '%s://%s%s' % (web.ctx['protocol'], web.ctx['host'], web.ctx['path']),
            'query_string': web.ctx.query,
            'method': web.ctx.method,
            'data': web.data(),
            'headers': dict(get_headers(web.ctx.environ)),
            'env': dict(get_environ(web.ctx.environ)),
        }
    }
