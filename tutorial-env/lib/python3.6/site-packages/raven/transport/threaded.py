"""
raven.transport.threaded
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import atexit
import logging
import threading
import os

from time import sleep, time

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport
from raven.utils.compat import Queue, check_threads

DEFAULT_TIMEOUT = 10

logger = logging.getLogger('sentry.errors')


class AsyncWorker(object):
    _terminator = object()

    def __init__(self, shutdown_timeout=DEFAULT_TIMEOUT):
        check_threads()
        self._queue = Queue(-1)
        self._lock = threading.Lock()
        self._thread = None
        self._thread_for_pid = None
        self.options = {
            'shutdown_timeout': shutdown_timeout,
        }
        self.start()

    def is_alive(self):
        if self._thread_for_pid != os.getpid():
            return False
        return self._thread and self._thread.is_alive()

    def _ensure_thread(self):
        if self.is_alive():
            return
        self.start()

    def main_thread_terminated(self):
        with self._lock:
            if not self.is_alive():
                # thread not started or already stopped - nothing to do
                return

            # wake the processing thread up
            self._queue.put_nowait(self._terminator)

            timeout = self.options['shutdown_timeout']

            # wait briefly, initially
            initial_timeout = min(0.1, timeout)

            if not self._timed_queue_join(initial_timeout):
                # if that didn't work, wait a bit longer
                # NB that size is an approximation, because other threads may
                # add or remove items
                size = self._queue.qsize()

                print("Sentry is attempting to send %i pending error messages"
                      % size)
                print("Waiting up to %s seconds" % timeout)

                if os.name == 'nt':
                    print("Press Ctrl-Break to quit")
                else:
                    print("Press Ctrl-C to quit")

                self._timed_queue_join(timeout - initial_timeout)

            self._thread = None

    def _timed_queue_join(self, timeout):
        """
        implementation of Queue.join which takes a 'timeout' argument

        returns true on success, false on timeout
        """
        deadline = time() + timeout
        queue = self._queue

        queue.all_tasks_done.acquire()
        try:
            while queue.unfinished_tasks:
                delay = deadline - time()
                if delay <= 0:
                    # timed out
                    return False

                queue.all_tasks_done.wait(timeout=delay)

            return True

        finally:
            queue.all_tasks_done.release()

    def start(self):
        """
        Starts the task thread.
        """
        self._lock.acquire()
        try:
            if not self.is_alive():
                self._thread = threading.Thread(target=self._target, name="raven.AsyncWorker")
                self._thread.setDaemon(True)
                self._thread.start()
                self._thread_for_pid = os.getpid()
        finally:
            self._lock.release()
            atexit.register(self.main_thread_terminated)

    def stop(self, timeout=None):
        """
        Stops the task thread. Synchronous!
        """
        with self._lock:
            if self._thread:
                self._queue.put_nowait(self._terminator)
                self._thread.join(timeout=timeout)
                self._thread = None
                self._thread_for_pid = None

    def queue(self, callback, *args, **kwargs):
        self._ensure_thread()
        self._queue.put_nowait((callback, args, kwargs))

    def _target(self):
        while True:
            record = self._queue.get()
            try:
                if record is self._terminator:
                    break
                callback, args, kwargs = record
                try:
                    callback(*args, **kwargs)
                except Exception:
                    logger.error('Failed processing job', exc_info=True)
            finally:
                self._queue.task_done()

            sleep(0)


class ThreadedHTTPTransport(AsyncTransport, HTTPTransport):

    scheme = ['http', 'https', 'threaded+http', 'threaded+https']

    def get_worker(self):
        if not hasattr(self, '_worker') or not self._worker.is_alive():
            self._worker = AsyncWorker()
        return self._worker

    def send_sync(self, url, data, headers, success_cb, failure_cb):
        try:
            super(ThreadedHTTPTransport, self).send(url, data, headers)
        except Exception as e:
            failure_cb(e)
        else:
            success_cb()

    def async_send(self, url, data, headers, success_cb, failure_cb):
        self.get_worker().queue(
            self.send_sync, url, data, headers, success_cb, failure_cb)
