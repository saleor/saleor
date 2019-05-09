from __future__ import absolute_import

from django.core.exceptions import ImproperlyConfigured
from django.template.base import TemplateSyntaxError


class BlockNotFound(TemplateSyntaxError):
    """The expected block was not found."""


class UnsupportedEngine(ImproperlyConfigured):
    """An engine that we cannot render blocks from was used."""
