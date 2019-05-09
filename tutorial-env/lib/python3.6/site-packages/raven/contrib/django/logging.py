"""
raven.contrib.django.logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import warnings

warnings.warn('raven.contrib.django.logging is deprecated. Use raven.contrib.django.handlers instead.', DeprecationWarning)

from raven.contrib.django.handlers import SentryHandler  # NOQA

__all__ = ('SentryHandler',)
