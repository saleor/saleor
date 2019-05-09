from concurrent.futures import ThreadPoolExecutor

from rx.core import Scheduler

from .newthreadscheduler import NewThreadScheduler


class ThreadPoolScheduler(NewThreadScheduler):
    """A scheduler that schedules work via the thread pool."""

    class ThreadPoolThread:
        """Wraps a concurrent future as a thread."""

        def __init__(self, executor, run):
            self.run = run
            self.future = None
            self.executor = executor

        def start(self):
            self.future = self.executor.submit(self.run)

        def cancel(self):
            self.future.cancel()

    def __init__(self, max_workers=None):
        super(ThreadPoolScheduler, self).__init__(self.thread_factory)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def thread_factory(self, target, *args):
        return self.ThreadPoolThread(self.executor, target)

Scheduler.thread_pool = thread_pool_scheduler = ThreadPoolScheduler()
