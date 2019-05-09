from rx import AnonymousObservable, Observable
from rx.disposables import SingleAssignmentDisposable, SerialDisposable, ScheduledDisposable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def subscribe_on(self, scheduler):
    """Subscribe on the specified scheduler.

    Wrap the source sequence in order to run its subscription and
    unsubscription logic on the specified scheduler. This operation is not
    commonly used; see the remarks section for more information on the
    distinction between subscribe_on and observe_on.

    Keyword arguments:
    scheduler -- Scheduler to perform subscription and unsubscription
        actions on.

    Returns the source sequence whose subscriptions and unsubscriptions
    happen on the specified scheduler.

    This only performs the side-effects of subscription and unsubscription
    on the specified scheduler. In order to invoke observer callbacks on a
    scheduler, use observe_on.
    """
    source = self

    def subscribe(observer):
        m = SingleAssignmentDisposable()
        d = SerialDisposable()
        d.disposable = m

        def action(scheduler, state):
            d.disposable = ScheduledDisposable(scheduler, source.subscribe(observer))

        m.disposable = scheduler.schedule(action)
        return d

    return AnonymousObservable(subscribe)
