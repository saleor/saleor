from rx.internal import Enumerable, Enumerator
from rx.internal import extensionclassmethod

@extensionclassmethod(Enumerable)
def while_do(cls, condition, source):
    def next():
        while condition(source):
            yield source

        raise StopIteration()
    return Enumerable(next())

