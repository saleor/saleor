from rx.internal.basic import default_comparer


class Recorded(object):
    def __init__(self, time, value, comparer=None):
        self.time = time
        self.value = value
        self.comparer = comparer or default_comparer

    def __eq__(self, other):
        """Returns true if a recorded value matches another recorded value"""

        time_match = self.time == other.time
        return time_match and self.comparer(self.value, other.value)

    equals = __eq__

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "%s@%s" % (self.value, self.time)
