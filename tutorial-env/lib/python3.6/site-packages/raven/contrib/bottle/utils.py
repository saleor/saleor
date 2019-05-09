"""
raven.contrib.bottle.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging
from raven.utils.compat import urlparse

from raven.utils.wsgi import get_headers, get_environ

logger = logging.getLogger(__name__)


def get_data_from_request(request):
    urlparts = urlparse.urlsplit(request.url)

    try:
        form_dict = request.forms.dict
        # we only are about the most recent one
        formdata = dict([(k, form_dict[k][-1]) for k in form_dict])
    except Exception:
        formdata = {}

    data = {
        'request': {
            'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': formdata,
            'headers': dict(get_headers(request.environ)),
            'env': dict(get_environ(request.environ)),
        }
    }

    return data
