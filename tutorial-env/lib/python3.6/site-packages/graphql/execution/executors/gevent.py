from __future__ import absolute_import

import gevent
from promise import Promise

from .utils import process


class GeventExecutor(object):
    def __init__(self):
        self.jobs = []

    def wait_until_finished(self):
        # gevent.joinall(self.jobs)
        while self.jobs:
            jobs = self.jobs
            self.jobs = []
            [j.join() for j in jobs]

    def clean(self):
        self.jobs = []

    def execute(self, fn, *args, **kwargs):
        promise = Promise()
        job = gevent.spawn(process, promise, fn, args, kwargs)
        self.jobs.append(job)
        return promise
