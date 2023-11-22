import collections


class CacheDict(collections.OrderedDict):
    def __init__(self, capacity: int):
        self.capacity = capacity
        super().__init__()

    def __getitem__(self, key):
        value = super().__getitem__(key)
        super().move_to_end(key)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        super().move_to_end(key)

        while len(self) > self.capacity:
            surplus = next(iter(self))
            super().__delitem__(surplus)
