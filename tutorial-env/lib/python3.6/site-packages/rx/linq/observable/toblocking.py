from rx.core import Observable
from rx.core.blockingobservable import BlockingObservable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def to_blocking(self):
    return BlockingObservable(self)
