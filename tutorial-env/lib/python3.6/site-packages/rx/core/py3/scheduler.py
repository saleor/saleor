from abc import ABCMeta, abstractmethod


class Scheduler(metaclass=ABCMeta):
    @property
    @abstractmethod
    def now(self):
        return NotImplemented

    @abstractmethod
    def schedule(self, action, state=None):
        return NotImplemented

    @abstractmethod
    def schedule_relative(self, duetime, action, state=None):
        return NotImplemented

    @abstractmethod
    def schedule_absolute(self, duetime, action, state=None):
        return NotImplemented
