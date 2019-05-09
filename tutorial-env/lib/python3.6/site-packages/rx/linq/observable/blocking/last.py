from rx.internal import extensionmethod

from rx.core.blockingobservable import BlockingObservable


@extensionmethod(BlockingObservable)
def last(self):
    """
    Blocks until the last element emits from a BlockingObservable.

    If no item is emitted when on_completed() is called, an exception is thrown

    Note: This will block even if the underlying Observable is asynchronous.

    :param self:
    :return: the last item to be emitted from a BlockingObservable
    """
    last_item = None
    is_empty = True

    for item in self.to_iterable():
        is_empty = False
        last_item = item

    if is_empty:
        raise Exception("No items were emitted")

    return last_item


@extensionmethod(BlockingObservable)
def last_or_default(self, default_value):
    """
    Blocks until the last element emits from a BlockingObservable.

    If no item is emitted when on_completed() is called, the provided default_value will be returned

    Note: This will block even if the underlying Observable is asynchronous.

    :param default_value:
    :param self:
    :return: the last item to be emitted from a BlockingObservable
    """
    last_item = None
    is_empty = True

    for item in self.to_iterable():
        is_empty = False
        last_item = item

    if is_empty:
        return default_value

    return last_item
