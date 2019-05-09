"""
raven.contrib.awslambda
~~~~~~~~~~~~~~~~~~~~

Raven wrapper for AWS Lambda handlers.

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
# flake8: noqa

from __future__ import absolute_import

import os
import logging
import functools
from types import FunctionType

from raven.base import Client
from raven.transport.http import HTTPTransport

logger = logging.getLogger('sentry.errors.client')


def get_default_tags():
    return {
        'lambda': 'AWS_LAMBDA_FUNCTION_NAME',
        'version': 'AWS_LAMBDA_FUNCTION_VERSION',
        'memory_size': 'AWS_LAMBDA_FUNCTION_MEMORY_SIZE',
        'log_group': 'AWS_LAMBDA_LOG_GROUP_NAME',
        'log_stream': 'AWS_LAMBDA_LOG_STREAM_NAME',
        'region': 'AWS_REGION'
    }


class LambdaClient(Client):
    """
    Raven decorator for AWS Lambda.

    By default, the lambda integration will capture unhandled exceptions and instrument logging.

    Usage:

    >>> from raven.contrib.awslambda import LambdaClient
    >>>
    >>>
    >>> client = LambdaClient()
    >>>
    >>> @client.capture_exceptions
    >>> def handler(event, context):
    >>>    ...
    >>>    raise Exception('I will be sent to sentry!')

    """

    def __init__(self, *args, **kwargs):
        transport = kwargs.pop('transport', HTTPTransport)
        super(LambdaClient, self).__init__(*args, transport=transport, **kwargs)

    def capture(self, *args, **kwargs):
        if 'data' not in kwargs:
            kwargs['data'] = data = {}
        else:
            data = kwargs['data']
        event = kwargs.get('event', None)
        context = kwargs.get('context', None)

        if event:
            http_info = self._get_http_interface(event)
            user_info = self._get_user_interface(event)
            if http_info:
                data.update(http_info)
            if user_info:
                data.update(user_info)

        if event and context:
            data['extra'] = self._get_extra_data(event, context)

        return super(LambdaClient, self).capture(*args, **kwargs)

    def build_msg(self, *args, **kwargs):

        data = super(LambdaClient, self).build_msg(*args, **kwargs)
        for option, default in get_default_tags().items():
            data['tags'].setdefault(option, os.environ.get(default))
        data.setdefault('release', os.environ.get('SENTRY_RELEASE'))
        data.setdefault('environment', os.environ.get('SENTRY_ENVIRONMENT'))
        return data

    def capture_exceptions(self, f=None, exceptions=None):  # TODO: Ash fix kwargs in base
        """
        Wrap a function or code block in try/except and automatically call
        ``.captureException`` if it raises an exception, then the exception
        is reraised.

        By default, it will capture ``Exception``

        >>> @client.capture_exceptions
        >>> def foo():
        >>>     raise Exception()

        >>> with client.capture_exceptions():
        >>>    raise Exception()

        You can also specify exceptions to be caught specifically

        >>> @client.capture_exceptions((IOError, LookupError))
        >>> def bar():
        >>>     ...

        ``kwargs`` are passed through to ``.captureException``.
        """
        if not isinstance(f, FunctionType):
            # when the decorator has args which is not a function we except
            # f to be the exceptions tuple
            return functools.partial(self.capture_exceptions, exceptions=f)

        exceptions = exceptions or (Exception,)

        @functools.wraps(f)
        def wrapped(event, context, *args, **kwargs):
            try:
                return f(event, context, *args, **kwargs)
            except exceptions:
                self.captureException(event=event, context=context, **kwargs)
                self.context.clear()
                raise
        return wrapped

    @staticmethod
    def _get_user_interface(event):
        if event.get('requestContext'):
            identity = event['requestContext']['identity']
            if identity:
                user = {
                    'id': identity.get('cognitoIdentityId', None) or identity.get('user', None),
                    'username': identity.get('user', None),
                    'ip_address': identity.get('sourceIp', None),
                    'cognito_identity_pool_id': identity.get('cognitoIdentityPoolId', None),
                    'cognito_authentication_type': identity.get('cognitoAuthenticationType', None),
                    'user_agent': identity.get('userAgent')
                }
                return {'user': user}

    @staticmethod
    def _get_http_interface(event):
        if event.get('path') and event.get('httpMethod'):
            request = {
                "url": event.get('path'),
                "method": event.get('httpMethod'),
                "query_string": event.get('queryStringParameters', None),
                "headers": event.get('headers', None) or [],
            }
            return {'request': request}

    @staticmethod
    def _get_extra_data(event, context):
        extra_context = {
            'event': event,
            'aws_request_id': context.aws_request_id,
            'context': vars(context),
        }

        if context.client_context:
            extra_context['client_context'] = {
                'client.installation_id': context.client_context.client.installation_id,
                'client.app_title': context.client_context.client.app_title,
                'client.app_version_name': context.client_context.client.app_version_name,
                'client.app_version_code': context.client_context.client.app_version_code,
                'client.app_package_name': context.client_context.client.app_package_name,
                'custom': context.client_context.custom,
                'env': context.client_context.env,
            }
        return extra_context



