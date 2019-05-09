from functools import total_ordering


@total_ordering
class OrderedType(object):
    creation_counter = 1

    def __init__(self, _creation_counter=None):
        self.creation_counter = _creation_counter or self.gen_counter()

    @staticmethod
    def gen_counter():
        counter = OrderedType.creation_counter
        OrderedType.creation_counter += 1
        return counter

    def reset_counter(self):
        self.creation_counter = self.gen_counter()

    def __eq__(self, other):
        # Needed for @total_ordering
        if isinstance(self, type(other)):
            return self.creation_counter == other.creation_counter
        return NotImplemented

    def __lt__(self, other):
        # This is needed because bisect does not take a comparison function.
        if isinstance(other, OrderedType):
            return self.creation_counter < other.creation_counter
        return NotImplemented

    def __gt__(self, other):
        # This is needed because bisect does not take a comparison function.
        if isinstance(other, OrderedType):
            return self.creation_counter > other.creation_counter
        return NotImplemented

    def __hash__(self):
        return hash((self.creation_counter))
