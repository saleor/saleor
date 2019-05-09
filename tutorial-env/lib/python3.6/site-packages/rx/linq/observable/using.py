from rx.core import Observable, AnonymousObservable, Disposable
from rx.disposables import CompositeDisposable
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable)
def using(cls, resource_factory, observable_factory):
    """Constructs an observable sequence that depends on a resource object,
    whose lifetime is tied to the resulting observable sequence's lifetime.

    1 - res = rx.Observable.using(lambda: AsyncSubject(), lambda: s: s)

    Keyword arguments:
    resource_factory -- Factory function to obtain a resource object.
    observable_factory -- Factory function to obtain an observable sequence
        that depends on the obtained resource.

    Returns an observable sequence whose lifetime controls the lifetime of
    the dependent resource object.
    """

    def subscribe(observer):
        disposable = Disposable.empty()
        try:
            resource = resource_factory()
            if resource:
                disposable = resource

            source = observable_factory(resource)
        except Exception as exception:
            d = Observable.throw_exception(exception).subscribe(observer)
            return CompositeDisposable(d, disposable)

        return CompositeDisposable(source.subscribe(observer), disposable)
    return AnonymousObservable(subscribe)
