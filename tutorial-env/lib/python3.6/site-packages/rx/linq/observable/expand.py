from rx.core import Observable, AnonymousObservable

from rx.disposables import SerialDisposable, CompositeDisposable, \
    SingleAssignmentDisposable
from rx.concurrency import immediate_scheduler
from rx.internal import extensionmethod


@extensionmethod(Observable)
def expand(self, selector, scheduler=None):
    """Expands an observable sequence by recursively invoking selector.

    selector -- {Function} Selector function to invoke for each produced
        element, resulting in another sequence to which the selector will be
        invoked recursively again.
    scheduler -- {Scheduler} [Optional] Scheduler on which to perform the
        expansion. If not provided, this defaults to the current thread
        scheduler.

    Returns an observable {Observable} sequence containing all the elements
    produced by the recursive expansion.
    """

    scheduler = scheduler or immediate_scheduler
    source = self

    def subscribe(observer):
        q = []
        m = SerialDisposable()
        d = CompositeDisposable(m)
        active_count = [0]
        is_acquired = [False]

        def ensure_active():
            is_owner = False
            if len(q) > 0:
                is_owner = not is_acquired[0]
                is_acquired[0] = True

            def action(scheduler, state):
                if len(q) > 0:
                    work = q.pop(0)
                else:
                    is_acquired[0] = False
                    return

                sad = SingleAssignmentDisposable()
                d.add(sad)

                def on_next(x):
                    observer.on_next(x)
                    result = None
                    try:
                        result = selector(x)
                    except Exception as ex:
                        observer.on_error(ex)

                    q.append(result)
                    active_count[0] += 1
                    ensure_active()

                def on_complete():
                    d.remove(sad)
                    active_count[0] -= 1
                    if active_count[0] == 0:
                        observer.on_completed()

                sad.disposable = work.subscribe(on_next, observer.on_error, on_complete)
                m.disposable = scheduler.schedule(action)

            if is_owner:
                m.disposable = scheduler.schedule(action)

        q.append(source)
        active_count[0] += 1
        ensure_active()
        return d
    return AnonymousObservable(subscribe)
