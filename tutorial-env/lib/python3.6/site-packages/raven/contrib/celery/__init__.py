"""
raven.contrib.celery
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging

from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import (
    after_setup_logger, task_failure, task_prerun, task_postrun
)
from raven.handlers.logging import SentryHandler


class CeleryFilter(logging.Filter):
    def filter(self, record):
        # Context is fixed in Celery 3.x so use internal flag instead
        extra_data = getattr(record, 'data', {})
        if not isinstance(extra_data, dict):
            return record.funcName != '_log_error'
        # Fallback to funcName for Celery 2.5
        return extra_data.get('internal', record.funcName != '_log_error')


def register_signal(client, ignore_expected=False):
    SentryCeleryHandler(client, ignore_expected=ignore_expected).install()


def register_logger_signal(client, logger=None, loglevel=logging.ERROR):
    filter_ = CeleryFilter()

    handler = SentryHandler(client)
    handler.setLevel(loglevel)
    handler.addFilter(filter_)

    def process_logger_event(sender, logger, loglevel, logfile, format,
                             colorize, **kw):
        # Attempt to find an existing SentryHandler, and if it exists ensure
        # that the CeleryFilter is installed.
        # If one is found, we do not attempt to install another one.
        for h in logger.handlers:
            if isinstance(h, SentryHandler):
                h.addFilter(filter_)
                return False

        logger.addHandler(handler)

    after_setup_logger.connect(process_logger_event, weak=False)


class SentryCeleryHandler(object):
    def __init__(self, client, ignore_expected=False):
        self.client = client
        self.ignore_expected = ignore_expected

    def install(self):
        task_prerun.connect(self.handle_task_prerun, weak=False)
        task_postrun.connect(self.handle_task_postrun, weak=False)
        task_failure.connect(self.process_failure_signal, weak=False)

    def uninstall(self):
        task_prerun.disconnect(self.handle_task_prerun)
        task_postrun.disconnect(self.handle_task_postrun)
        task_failure.disconnect(self.process_failure_signal)

    def process_failure_signal(self, sender, task_id, args, kwargs, einfo, **kw):
        if self.ignore_expected and hasattr(sender, 'throws') and isinstance(einfo.exception, sender.throws):
            return

        # This signal is fired inside the stack so let raven do its magic
        if isinstance(einfo.exception, SoftTimeLimitExceeded):
            fingerprint = ['celery', 'SoftTimeLimitExceeded', getattr(sender, 'name', sender)]
        else:
            fingerprint = None

        self.client.captureException(
            extra={
                'task_id': task_id,
                'task': sender,
                'args': args,
                'kwargs': kwargs,
            },
            fingerprint=fingerprint,
        )

    def handle_task_prerun(self, sender, task_id, task, **kw):
        self.client.context.activate()
        self.client.transaction.push(task.name)

    def handle_task_postrun(self, sender, task_id, task, **kw):
        self.client.transaction.pop(task.name)
        self.client.context.clear()
