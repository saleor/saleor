"""
raven.contrib.paste
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.middleware import Sentry
from raven.base import Client


def sentry_filter_factory(app, global_conf, **kwargs):
    client = Client(**kwargs)
    return Sentry(app, client)
