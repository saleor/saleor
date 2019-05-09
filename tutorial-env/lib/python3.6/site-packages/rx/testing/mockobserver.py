from rx.core import Observer
from rx.core.notification import OnNext, OnError, OnCompleted

from .recorded import Recorded
from .reactive_assert import AssertList


class MockObserver(Observer):

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.messages = AssertList()

    def on_next(self, value):
        self.messages.append(Recorded(self.scheduler.clock, OnNext(value)))

    def on_error(self, exception):
        self.messages.append(Recorded(self.scheduler.clock, OnError(exception)))

    def on_completed(self):
        self.messages.append(Recorded(self.scheduler.clock, OnCompleted()))
