"""
raven.contrib.django.middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging
import threading

from django.conf import settings
from django.core.signals import request_finished

try:
    # Django >= 1.10
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Not required for Django <= 1.9, see:
    # https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    MiddlewareMixin = object


def is_ignorable_404(uri):
    """
    Returns True if a 404 at the given URL *shouldn't* notify the site managers.
    """
    return any(
        pattern.search(uri)
        for pattern in getattr(settings, 'IGNORABLE_404_URLS', ())
    )


class Sentry404CatchMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code != 404:
            return response

        if is_ignorable_404(request.get_full_path()):
            return response

        from raven.contrib.django.models import client

        if not client.is_enabled():
            return response

        data = client.get_data_from_request(request)
        data.update({
            'level': logging.INFO,
            'logger': 'http404',
        })
        result = client.captureMessage(message='Page Not Found: %s' % request.build_absolute_uri(), data=data)
        if not result:
            return

        request.sentry = {
            'project_id': data.get('project', client.remote.project),
            'id': client.get_ident(result),
        }
        return response

    # sentry_exception_handler(sender=Sentry404CatchMiddleware, request=request)


class SentryResponseErrorIdMiddleware(MiddlewareMixin):
    """
    Appends the X-Sentry-ID response header for referencing a message within
    the Sentry datastore.
    """

    def process_response(self, request, response):
        if not getattr(request, 'sentry', None):
            return response
        response['X-Sentry-ID'] = request.sentry['id']
        return response


class SentryMiddleware(MiddlewareMixin):
    thread = threading.local()

    def process_request(self, request):
        self._txid = None

        SentryMiddleware.thread.request = request
        # we utilize request_finished as the exception gets reported
        # *after* process_response is executed, and thus clearing the
        # transaction there would leave it empty
        # XXX(dcramer): weakref's cause a threading issue in certain
        # versions of Django (e.g. 1.6). While they'd be ideal, we're under
        # the assumption that Django will always call our function except
        # in the situation of a process or thread dying.
        request_finished.connect(self.request_finished, weak=False)

    def process_view(self, request, func, args, kwargs):
        from raven.contrib.django.models import client

        try:
            self._txid = client.transaction.push(
                client.get_transaction_from_request(request)
            )
        except Exception as exc:
            client.error_logger.exception(repr(exc), extra={'request': request})

        return None

    def request_finished(self, **kwargs):
        from raven.contrib.django.models import client

        if getattr(self, '_txid', None):
            client.transaction.pop(self._txid)
            self._txid = None

        SentryMiddleware.thread.request = None

        request_finished.disconnect(self.request_finished)


SentryLogMiddleware = SentryMiddleware


class DjangoRestFrameworkCompatMiddleware(MiddlewareMixin):

    non_cacheable_types = (
        'application/x-www-form-urlencoded',
        'multipart/form-data',
        'application/octet-stream'
    )

    def process_request(self, request):
        """
        Access request.body, otherwise it might not be accessible later
        after request has been read/streamed
        """
        content_type = request.META.get('CONTENT_TYPE', '')
        for non_cacheable_type in self.non_cacheable_types:
            if non_cacheable_type in content_type:
                return
        request.body  # forces stream to be read into memory
