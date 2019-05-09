from abc import ABCMeta, abstractmethod


class Observable(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def subscribe(self, observer):
        return NotImplemented
