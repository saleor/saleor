# -*- coding: utf-8 -*-
"""
raven.contrib.zope
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from inspect import getouterframes, currentframe, getinnerframes
from raven.handlers.logging import SentryHandler
from ZConfig.components.logger.factory import Factory
import logging
from AccessControl.users import nobody
from raven.utils.stacks import iter_stack_frames

logger = logging.getLogger(__name__)


class ZopeSentryHandlerFactory(Factory):

    def getLevel(self):
        return self.section.level

    def create(self):
        return ZopeSentryHandler(**self.section.__dict__)

    def __init__(self, section):
        Factory.__init__(self)
        self.section = section


class ZopeSentryHandler(SentryHandler):
    """
    Zope unfortunately eats the stack trace information.
    To get the stack trace information and other useful information
    from the request object, this class looks into the different stack
    frames when the emit method is invoked.
    """

    def __init__(self, *args, **kw):
        super(ZopeSentryHandler, self).__init__(*args, **kw)
        level = kw.get('level', logging.ERROR)
        self.setLevel(level)

    def can_record(self, record):
        return not (
            record.name == 'raven' or
            record.name.startswith(('sentry.errors', 'raven.'))
        )

    def emit(self, record):
        if record.levelno <= logging.ERROR and self.can_record(record):
            request = None
            exc_info = None
            for frame_info in getouterframes(currentframe()):
                frame = frame_info[0]
                if not request:
                    request = frame.f_locals.get('request', None)
                    if not request:
                        view = frame.f_locals.get('self', None)
                        try:
                            request = getattr(view, 'request', None)
                        except RuntimeError:
                            request = None
                if not exc_info:
                    exc_info = frame.f_locals.get('exc_info', None)
                    if not hasattr(exc_info, '__getitem__'):
                        exc_info = None
                if request and exc_info:
                    break

            if exc_info:
                record.exc_info = exc_info
                record.stack = \
                    iter_stack_frames(getinnerframes(exc_info[2]))
            if request:
                try:
                    body_pos = request.stdin.tell()
                    request.stdin.seek(0)
                    body = request.stdin.read()
                    request.stdin.seek(body_pos)
                    http = dict(headers=request.environ,
                                url=request.getURL(),
                                method=request.method,
                                host=request.environ.get('REMOTE_ADDR',
                                ''), data=body)
                    if 'HTTP_USER_AGENT' in http['headers']:
                        if 'User-Agent' not in http['headers']:
                            http['headers']['User-Agent'] = \
                                http['headers']['HTTP_USER_AGENT']
                    if 'QUERY_STRING' in http['headers']:
                        http['query_string'] = http['headers']['QUERY_STRING']
                    setattr(record, 'request', http)
                    user = request.get('AUTHENTICATED_USER', None)
                    if user is not None and user != nobody:
                        user_dict = {
                            'id': user.getId(),
                            'email': user.getProperty('email') or '',
                        }
                    else:
                        user_dict = {}
                    setattr(record, 'user', user_dict)
                except (AttributeError, KeyError):
                    logger.warning('Could not extract data from request', exc_info=True)
        return super(ZopeSentryHandler, self).emit(record)
