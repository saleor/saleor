from rx.internal import extensionmethod

from rx.core.blockingobservable import BlockingObservable


@extensionmethod(BlockingObservable)
def first(self):
    """
    Blocks until the first element emits from a BlockingObservable.

    If no item is emitted when on_completed() is called, an exception is thrown

    Note: This will block even if the underlying Observable is asynchronous.

    :param self:
    :return: the first item to be emitted from a BlockingObservable
    """
    return next(self.to_iterable())


@extensionmethod(BlockingObservable)
def first_or_default(self, default_value):
    """
    Blocks until the first element emits from a BlockingObservable.

    If no item is emitted when on_completed() is called, the provided default_value is returned instead

    Note: This will block even if the underlying Observable is asynchronous.

    :param default_value:
    :param self:
    :return: the first item to be emitted from a BlockingObservable
    """
    return next(self.to_iterable(), default_value)


