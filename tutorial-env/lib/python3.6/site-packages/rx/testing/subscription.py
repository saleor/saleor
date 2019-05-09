import sys


class Subscription(object):
    def __init__(self, start, end=None):
        self.subscribe = start
        self.unsubscribe = end or sys.maxsize

    def equals(self, other):
        return self.subscribe == other.subscribe and self.unsubscribe == other.unsubscribe

    def __eq__(self, other):
        return self.equals(other)

    def __repr__(self):
        return str(self)

    def __str__(self):
        unsubscribe = "Infinite" if self.unsubscribe == sys.maxsize else self.unsubscribe
        return "(%s, %s)" % (self.subscribe, unsubscribe)
