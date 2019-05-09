"""Utilities."""
# -- XXX This module must not use translation as that causes
# -- a recursive loader import!
from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.utils import timezone

# see Issue celery/django-celery#222
now_localtime = getattr(timezone, 'template_localtime', timezone.localtime)


def now():
    """Return the current date and time."""
    if getattr(settings, 'USE_TZ', False):
        return now_localtime(timezone.now())
    else:
        return timezone.now()
