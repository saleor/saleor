class Enumerator(object):
    """For Python we just wrap the iterator"""

    def __init__(self, next):
        self.iterator = next

    def __next__(self):
        return next(self.iterator)

    # Python 2.7
    next = __next__

    def __iter__(self):
        return self
