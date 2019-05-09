from __future__ import absolute_import

import copy
import os

from raven.utils.compat import string_types
from raven.utils.imports import import_string


def convert_options(settings, defaults=None):
    """
    Convert a settings object (or dictionary) to parameters which may be passed
    to a new ``Client()`` instance.
    """
    if defaults is None:
        defaults = {}

    if isinstance(settings, dict):
        def getopt(key, default=None):
            return settings.get(
                'SENTRY_%s' % key.upper(),
                defaults.get(key, default)
            )

        options = copy.copy(
            settings.get('SENTRY_CONFIG')
            or settings.get('RAVEN_CONFIG')
            or {}
        )
    else:
        def getopt(key, default=None):
            return getattr(settings, 'SENTRY_%s' % key.upper(), defaults.get(key, default))

        options = copy.copy(
            getattr(settings, 'SENTRY_CONFIG', None)
            or getattr(settings, 'RAVEN_CONFIG', None)
            or {}
        )

    options.setdefault('include_paths', getopt('include_paths', []))
    options.setdefault('exclude_paths', getopt('exclude_paths', []))
    options.setdefault('timeout', getopt('timeout'))
    options.setdefault('name', getopt('name'))
    options.setdefault('auto_log_stacks', getopt('auto_log_stacks'))
    options.setdefault('string_max_length', getopt('string_max_length'))
    options.setdefault('list_max_length', getopt('list_max_length'))
    options.setdefault('site', getopt('site'))
    options.setdefault('processors', getopt('processors'))
    options.setdefault('sanitize_keys', getopt('sanitize_keys'))
    options.setdefault('dsn', getopt('dsn', os.environ.get('SENTRY_DSN')))
    options.setdefault('context', getopt('context'))
    options.setdefault('tags', getopt('tags'))
    options.setdefault('release', getopt('release'))
    options.setdefault('repos', getopt('repos'))
    options.setdefault('environment', getopt('environment'))
    options.setdefault('ignore_exceptions', getopt('ignore_exceptions'))
    options.setdefault('sample_rate', getopt('sample_rate'))

    transport = getopt('transport') or options.get('transport')
    if isinstance(transport, string_types):
        transport = import_string(transport)
    options['transport'] = transport

    return options
