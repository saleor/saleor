from __future__ import absolute_import, unicode_literals
from .celeryconf import app as celery_app

__all__ = ['celery_app']
__version__ = 'dev'
