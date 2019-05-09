"""
raven.conf
~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging

__all__ = ['setup_logging']

EXCLUDE_LOGGER_DEFAULTS = (
    'raven',
    'gunicorn',
    'south',
    'sentry.errors',
    'django.request',
    # dill produces a lot of garbage debug logs that are just a stream of what
    # another developer would use print/pdb for
    'dill',
)


def setup_logging(handler, exclude=EXCLUDE_LOGGER_DEFAULTS):
    """
    Configures logging to pipe to Sentry.

    - ``exclude`` is a list of loggers that shouldn't go to Sentry.

    For a typical Python install:

    >>> from raven.handlers.logging import SentryHandler
    >>> client = Sentry(...)
    >>> setup_logging(SentryHandler(client))

    Within Django:

    >>> from raven.contrib.django.handlers import SentryHandler
    >>> setup_logging(SentryHandler())

    Returns a boolean based on if logging was configured or not.
    """
    logger = logging.getLogger()
    if handler.__class__ in map(type, logger.handlers):
        return False

    logger.addHandler(handler)

    # Add StreamHandler to sentry's default so you can catch missed exceptions
    for logger_name in exclude:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
        logger.addHandler(logging.StreamHandler())

    return True
