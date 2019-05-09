"""Application configuration."""
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

__all__ = ['CeleryResultConfig']


class CeleryResultConfig(AppConfig):
    """Default configuration for the django_celery_results app."""

    name = 'django_celery_results'
    label = 'django_celery_results'
    verbose_name = _('Celery Results')
