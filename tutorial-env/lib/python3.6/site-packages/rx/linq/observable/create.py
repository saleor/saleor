from rx.core import Observable, AnonymousObservable
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable, alias="create_with_disposable")
def create(cls, subscribe):
    return AnonymousObservable(subscribe)
