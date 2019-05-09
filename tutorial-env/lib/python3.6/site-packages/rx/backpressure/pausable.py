
from rx.core import Observable, ObservableBase, Disposable
from rx.internal import extensionmethod
from rx.disposables import CompositeDisposable
from rx.subjects import Subject


class PausableObservable(ObservableBase):
    def __init__(self, source, pauser=None):
        self.source = source
        self.controller = Subject()

        if pauser and hasattr(pauser, "subscribe"):
            self.pauser = self.controller.merge(pauser)
        else:
            self.pauser = self.controller

        super(PausableObservable, self).__init__()

    def _subscribe_core(self, observer):
        conn = self.source.publish()
        subscription = conn.subscribe(observer)
        connection = [Disposable.empty()]

        def on_next(b):
            if b:
                connection[0] = conn.connect()
            else:
                connection[0].dispose()
                connection[0] = Disposable.empty()

        pausable = self.pauser.distinct_until_changed().subscribe(on_next)
        return CompositeDisposable(subscription, connection[0], pausable)

    def pause(self):
        self.controller.on_next(False)

    def resume(self):
        self.controller.on_next(True)


@extensionmethod(Observable)
def pausable(self, pauser):
    """Pauses the underlying observable sequence based upon the observable
    sequence which yields True/False.

    Example:
    pauser = rx.Subject()
    source = rx.Observable.interval(100).pausable(pauser)

    Keyword parameters:
    pauser -- {Observable} The observable sequence used to pause the
        underlying sequence.

    Returns the observable {Observable} sequence which is paused based upon
    the pauser.
    """

    return PausableObservable(self, pauser)
