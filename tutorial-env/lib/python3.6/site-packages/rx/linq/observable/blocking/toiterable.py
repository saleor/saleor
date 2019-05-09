from rx.core.blockingobservable import BlockingObservable
from rx.internal import extensionmethod
from rx.internal.enumerator import Enumerator
from rx import config


@extensionmethod(BlockingObservable)
def to_iterable(self):
    """Returns an iterator that can iterate over items emitted by this
    `BlockingObservable`.

    :returns: An iterator that can iterate over the items emitted by this
        `BlockingObservable`.
    :rtype: Iterable[Any]
    """

    condition = config["concurrency"].Condition()
    notifications = []

    def on_next(value):
        """Takes on_next values and appends them to the notification queue"""

        condition.acquire()
        notifications.append(value)
        condition.notify()  # signal that a new item is available
        condition.release()

    self.observable.materialize().subscribe(on_next)

    def gen():
        """Generator producing values for the iterator"""

        while True:
            condition.acquire()
            while not len(notifications):
                condition.wait()
            notification = notifications.pop(0)

            if notification.kind == "E":
                raise notification.exception

            if notification.kind == "C":
                return  # StopIteration

            condition.release()
            yield notification.value

    return Enumerator(gen())


@extensionmethod(BlockingObservable)
def __iter__(self):
    """Returns an iterator that can iterate over items emitted by this
    `BlockingObservable`.

    :param BlockingObservable self: Blocking observable instance.
    :returns: An iterator that can iterate over the items emitted by this
        `BlockingObservable`.
    :rtype: Iterable[Any]
    """

    return self.to_iterable()
