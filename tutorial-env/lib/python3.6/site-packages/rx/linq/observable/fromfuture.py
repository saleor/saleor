from rx.core import Observable, AnonymousObservable
from rx.internal.utils import is_future
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable)
def from_future(cls, future):
    """Converts a Future to an Observable sequence

    Keyword Arguments:
    future -- {Future} A Python 3 compatible future.
        https://docs.python.org/3/library/asyncio-task.html#future
        http://www.tornadoweb.org/en/stable/concurrent.html#tornado.concurrent.Future

    Returns {Observable} An Observable sequence which wraps the existing
    future success and failure.
    """

    def subscribe(observer):
        def done(future):
            try:
                value = future.result()
            except Exception as ex:
                observer.on_error(ex)
            else:
                observer.on_next(value)
                observer.on_completed()

        future.add_done_callback(done)

        def dispose():
            if future and future.cancel:
                future.cancel()

        return dispose

    return AnonymousObservable(subscribe) if is_future(future) else future
