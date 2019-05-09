from rx.core.blockingobservable import BlockingObservable
from rx.internal import extensionmethod
from rx.internal.utils import adapt_call
from rx import config


@extensionmethod(BlockingObservable)
def for_each(self, action):
    """Invokes a method on each item emitted by this BlockingObservable and
    blocks until the Observable completes.

    Note: This will block even if the underlying Observable is asynchronous.

    This is similar to Observable#subscribe(subscriber), but it blocks. Because
    it blocks it does not need the Subscriber#on_completed() or
    Subscriber#on_error(Throwable) methods. If the underlying Observable
    terminates with an error, rather than calling `onError`, this method will
    throw an exception.

    Keyword arguments:
    :param types.FunctionType action: the action to invoke for each item
        emitted by the `BlockingObservable`.
    :raises Exception: if an error occurs
    :returns: None
    :rtype: None
    """

    action = adapt_call(action)
    latch = config["concurrency"].Event()
    exception = [None]
    count = [0]

    def on_next(value):
        with self.lock:
            i = count[0]
            count[0] += 1
        action(value, i)

    def on_error(err):
        # If we receive an on_error event we set the reference on the
        # outer thread so we can git it and throw after the latch.wait()
        #
        # We do this instead of throwing directly since this may be on
        # a different thread and the latch is still waiting.
        exception[0] = err
        latch.set()

    def on_completed():
        latch.set()

    self.observable.subscribe(on_next, on_error, on_completed)

    # Block until the subscription completes and then return
    latch.wait()

    if exception[0] is not None:
        raise Exception(exception[0])
