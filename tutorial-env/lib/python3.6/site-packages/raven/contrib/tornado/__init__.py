"""
raven.contrib.tornado
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details
:license: BSD, see LICENSE for more details
"""
from __future__ import absolute_import

from functools import partial

from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.web import HTTPError as WebHTTPError

from raven.base import Client


class AsyncSentryClient(Client):
    """
    A mixin class that could be used along with request handlers to
    asynchronously send errors to sentry. The client also captures the
    information from the request handlers
    """

    def __init__(self, *args, **kwargs):
        self.validate_cert = kwargs.pop('validate_cert', True)
        super(AsyncSentryClient, self).__init__(*args, **kwargs)

    def capture(self, *args, **kwargs):
        """
        Takes the same arguments as the super function in :py:class:`Client`
        and extracts the keyword argument callback which will be called on
        asynchronous sending of the request

        :return: a 32-length string identifying this event
        """
        if not self.is_enabled():
            return

        data = self.build_msg(*args, **kwargs)

        future = self.send(callback=kwargs.get('callback', None), **data)

        return (data['event_id'], future)

    def send(self, auth_header=None, callback=None, **data):
        """
        Serializes the message and passes the payload onto ``send_encoded``.
        """
        message = self.encode(data)

        return self.send_encoded(message, auth_header=auth_header, callback=callback)

    def send_remote(self, url, data, headers=None, callback=None):
        if headers is None:
            headers = {}

        if not self.state.should_try():
            data = self.decode(data)
            self._log_failed_submission(data)
            return

        future = self._send_remote(
            url=url, data=data, headers=headers, callback=callback
        )
        ioloop.IOLoop.current().add_future(future, partial(self._handle_result, url, data))
        return future

    def _handle_result(self, url, data, future):
        try:
            future.result()
        except HTTPError as e:
            data = self.decode(data)
            self._failed_send(e, url, data)
        except Exception as e:
            data = self.decode(data)
            self._failed_send(e, url, data)
        else:
            self.state.set_success()

    def _send_remote(self, url, data, headers=None, callback=None):
        """
        Initialise a Tornado AsyncClient and send the request to the sentry
        server. If the callback is a callable, it will be called with the
        response.
        """
        if headers is None:
            headers = {}

        return AsyncHTTPClient().fetch(
            url, callback, method="POST", body=data, headers=headers,
            validate_cert=self.validate_cert
        )


class SentryMixin(object):
    """
    A mixin class that extracts information from the Request in a Request
    Handler to capture and send to sentry. This mixin class is designed to be
    used along with `tornado.web.RequestHandler`

    .. code-block:: python
        :emphasize-lines: 6

        class MyRequestHandler(SentryMixin, tornado.web.RequestHandler):
            def get(self):
                try:
                    fail()
                except Exception as e:
                    self.captureException()


    While the above example would result in sequential execution, an example
    for asynchronous use would be

    .. code-block:: python
        :emphasize-lines: 6

        class MyRequestHandler(SentryMixin, tornado.web.RequestHandler):

            @tornado.web.asynchronous
            @tornado.gen.engine
            def get(self):
                # Do something and record a message in sentry
                response = yield tornado.gen.Task(
                    self.captureMessage, "Did something really important"
                )
                self.write("Your request to do something important is done")
                self.finish()


    The mixin assumes that the application will have an attribute called
    `sentry_client`, which should be an instance of
    :py:class:`AsyncSentryClient`. This can be changed by implementing your
    own get_sentry_client method on your request handler.
    """

    def get_sentry_client(self):
        """
        Returns the sentry client configured in the application. If you need
        to change the behaviour to do something else to get the client, then
        subclass this method
        """
        return self.application.sentry_client

    def get_sentry_data_from_request(self):
        """
        Extracts the data required for 'sentry.interfaces.Http' from the
        current request being handled by the request handler

        :param return: A dictionary.
        """
        return {
            'request': {
                'url': self.request.full_url(),
                'method': self.request.method,
                'data': self.request.body,
                'query_string': self.request.query,
                'cookies': self.request.headers.get('Cookie', None),
                'headers': dict(self.request.headers),
            }
        }

    def get_sentry_user_info(self):
        """
        Data for sentry.interfaces.User

        Default implementation only sends `is_authenticated` by checking if
        `tornado.web.RequestHandler.get_current_user` tests postitively for on
        Truth calue testing
        """
        try:
            user = self.get_current_user()
        except Exception:
            return {}
        return {
            'user': {
                'is_authenticated': True if user else False
            }
        }

    def get_sentry_extra_info(self):
        """
        Subclass and implement this method if you need to send any extra
        information
        """
        return {
            'extra': {
            }
        }

    def get_default_context(self):
        data = {}

        # Update request data
        data.update(self.get_sentry_data_from_request())

        # update user data
        data.update(self.get_sentry_user_info())

        # Update extra data
        data.update(self.get_sentry_extra_info())

        return data

    def _capture(self, call_name, data=None, **kwargs):
        if data is None:
            data = self.get_default_context()
        else:
            default_context = self.get_default_context()
            if isinstance(data, dict):
                default_context.update(data)
            else:
                default_context['extra']['extra_data'] = data
            data = default_context

        client = self.get_sentry_client()

        return getattr(client, call_name)(data=data, **kwargs)

    def captureException(self, exc_info=None, **kwargs):
        return self._capture('captureException', exc_info=exc_info, **kwargs)

    def captureMessage(self, message, **kwargs):
        return self._capture('captureMessage', message=message, **kwargs)

    def log_exception(self, typ, value, tb):
        """Override implementation to report all exceptions to sentry.
        log_exception() is added in Tornado v3.1.
        """
        rv = super(SentryMixin, self).log_exception(typ, value, tb)
        # Do not capture tornado.web.HTTPErrors outside the 500 range.
        if isinstance(value, WebHTTPError) and (value.status_code < 500 or value.status_code > 599):
            return rv
        self.captureException(exc_info=(typ, value, tb))
        return rv

    def send_error(self, status_code=500, **kwargs):
        """Override implementation to report all exceptions to sentry, even
        after self.flush() or self.finish() is called, for pre-v3.1 Tornado.
        """
        if hasattr(super(SentryMixin, self), 'log_exception'):
            return super(SentryMixin, self).send_error(status_code, **kwargs)
        else:
            rv = super(SentryMixin, self).send_error(status_code, **kwargs)
            if 500 <= status_code <= 599:
                self.captureException(exc_info=kwargs.get('exc_info'))
            return rv
