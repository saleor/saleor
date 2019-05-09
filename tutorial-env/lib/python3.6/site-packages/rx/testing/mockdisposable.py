from .reactive_assert import AssertList


class MockDisposable():
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.disposes = AssertList()
        self.disposes.append(self.scheduler.clock)

    def dispose(self):
        self.disposes.append(self.scheduler.clock)
