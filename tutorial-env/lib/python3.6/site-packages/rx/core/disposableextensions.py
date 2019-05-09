from rx.core import Disposable
from rx.internal import noop, extensionclassmethod
from rx.disposables import AnonymousDisposable


@extensionclassmethod(Disposable)
def empty(cls):
    return AnonymousDisposable(noop)


@extensionclassmethod(Disposable)
def create(cls, action):
    return AnonymousDisposable(action)
