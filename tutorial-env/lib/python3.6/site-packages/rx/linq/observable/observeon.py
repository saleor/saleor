from rx.core import AnonymousObservable, Observable
from rx.internal import extensionmethod
from rx.core.observeonobserver import ObserveOnObserver


@extensionmethod(Observable)
def observe_on(self, scheduler):
    """Wraps the source sequence in order to run its observer callbacks on
    the specified scheduler.

    Keyword arguments:
    scheduler -- Scheduler to notify observers on.

    Returns the source sequence whose observations happen on the specified
    scheduler.

    This only invokes observer callbacks on a scheduler. In case the
    subscription and/or unsubscription actions have side-effects
    that require to be run on a scheduler, use subscribe_on.
    """

    source = self

    def subscribe(observer):
        return source.subscribe(ObserveOnObserver(scheduler, observer))

    return AnonymousObservable(subscribe)
