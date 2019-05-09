"""
raven.contrib.zerorpc
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import inspect

from raven.base import Client


class SentryMiddleware(object):
    """Sentry/Raven middleware for ZeroRPC.

    >>> import zerorpc
    >>> from raven.contrib.zerorpc import SentryMiddleware
    >>> sentry = SentryMiddleware(dsn='udp://..../')
    >>> zerorpc.Context.get_instance().register_middleware(sentry)

    Exceptions detected server-side in ZeroRPC will be submitted to Sentry (and
    propagated to the client as well).
    """

    def __init__(self, hide_zerorpc_frames=True, client=None, **kwargs):
        """
        Create a middleware object that can be injected in a ZeroRPC server.

        - hide_zerorpc_frames: modify the exception stacktrace to remove the
                               internal zerorpc frames (True by default to make
                               the stacktrace as readable as possible);
        - client: use an existing raven.Client object, otherwise one will be
                  instantiated from the keyword arguments.
        """
        self._sentry_client = client or Client(**kwargs)
        self._hide_zerorpc_frames = hide_zerorpc_frames

    def server_inspect_exception(self, req_event, rep_event, task_ctx, exc_info):
        """
        Called when an exception has been raised in the code run by ZeroRPC
        """
        # Hide the zerorpc internal frames for readability, for a REQ/REP or
        # REQ/STREAM server the frames to hide are:
        # - core.ServerBase._async_task
        # - core.Pattern*.process_call
        # - core.DecoratorBase.__call__
        #
        # For a PUSH/PULL or PUB/SUB server the frame to hide is:
        # - core.Puller._receiver
        if self._hide_zerorpc_frames:
            traceback = exc_info[2]
            while traceback:
                zerorpc_frame = traceback.tb_frame
                zerorpc_frame.f_locals['__traceback_hide__'] = True
                frame_info = inspect.getframeinfo(zerorpc_frame)
                # Is there a better way than this (or looking up the filenames
                # or hardcoding the number of frames to skip) to know when we
                # are out of zerorpc?
                if frame_info.function == '__call__' \
                        or frame_info.function == '_receiver':
                    break
                traceback = traceback.tb_next

        self._sentry_client.captureException(
            exc_info,
            extra=task_ctx
        )
