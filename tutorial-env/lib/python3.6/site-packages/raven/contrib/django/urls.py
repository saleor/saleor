"""
raven.contrib.django.urls
~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

try:
    from django.conf.urls import url
except ImportError:
    # for Django version less than 1.4
    from django.conf.urls.defaults import url  # NOQA

import raven.contrib.django.views

urlpatterns = (
    url(r'^api/(?P<project_id>[\w_-]+)/store/$', raven.contrib.django.views.report, name='raven-report'),
    url(r'^report/', raven.contrib.django.views.report),
)
