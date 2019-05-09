from multiprocessing import Process, Queue

from promise import Promise

from .utils import process


def queue_process(q):
    promise, fn, args, kwargs = q.get()
    process(promise, fn, args, kwargs)


class ProcessExecutor(object):
    def __init__(self):
        self.processes = []
        self.q = Queue()

    def wait_until_finished(self):
        while self.processes:
            processes = self.processes
            self.processes = []
            [_process.join() for _process in processes]
        self.q.close()
        self.q.join_thread()

    def clean(self):
        self.processes = []

    def execute(self, fn, *args, **kwargs):
        promise = Promise()

        self.q.put([promise, fn, args, kwargs], False)
        _process = Process(target=queue_process, args=(self.q))
        _process.start()
        self.processes.append(_process)
        return promise
