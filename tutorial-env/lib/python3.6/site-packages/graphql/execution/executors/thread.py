from multiprocessing.pool import ThreadPool
from threading import Thread

from promise import Promise
from .utils import process

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Callable, List


class ThreadExecutor(object):

    pool = None

    def __init__(self, pool=False):
        # type: (bool) -> None
        self.threads = []  # type: List[Thread]
        if pool:
            self.execute = self.execute_in_pool
            self.pool = ThreadPool(processes=pool)
        else:
            self.execute = self.execute_in_thread

    def wait_until_finished(self):
        # type: () -> None
        while self.threads:
            threads = self.threads
            self.threads = []
            for thread in threads:
                thread.join()

    def clean(self):
        self.threads = []

    def execute_in_thread(self, fn, *args, **kwargs):
        # type: (Callable, *Any, **Any) -> Promise
        promise = Promise()
        thread = Thread(target=process, args=(promise, fn, args, kwargs))
        thread.start()
        self.threads.append(thread)
        return promise

    def execute_in_pool(self, fn, *args, **kwargs):
        promise = Promise()
        self.pool.map(lambda input: process(*input), [(promise, fn, args, kwargs)])
        return promise
