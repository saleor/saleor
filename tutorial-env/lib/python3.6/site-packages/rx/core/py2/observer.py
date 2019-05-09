from abc import ABCMeta, abstractmethod


class Observer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_next(self, value):
        return NotImplemented

    @abstractmethod
    def on_error(self, error):
        return NotImplemented

    @abstractmethod
    def on_completed(self):
        return NotImplemented
