from rx.core import Observable
from rx.core import ObservableBase
from rx.internal.basic import noop
from rx.subjects import AsyncSubject
from rx.disposables import CompositeDisposable
from rx.concurrency import immediate_scheduler, current_thread_scheduler
from rx.internal import extensionmethod


class ChainObservable(ObservableBase):

    def _subscribe_core(self, observer):
        g = CompositeDisposable()

        def action(scheduler, state):
            observer.on_next(self.head)
            g.add(self.tail.merge_observable().subscribe(observer))

        g.add(current_thread_scheduler.schedule(action))
        return g

    def __init__(self, head):
        super(ChainObservable, self).__init__()
        self.head = head
        self.tail = AsyncSubject()

    def on_completed(self):
        self.on_next(Observable.empty())

    def on_error(self, e):
        self.on_next(Observable.throw_exception(e))

    def on_next(self, v):
        self.tail.on_next(v)
        self.tail.on_completed()


@extensionmethod(Observable)
def many_select(self, selector, scheduler=None):
    """Comonadic bind operator. Internally projects a new observable for each
    value, and it pushes each observable into the user-defined selector function
    that projects/queries each observable into some result.

    Keyword arguments:
    selector -- {Function} A transform function to apply to each element.
    scheduler -- {Object} [Optional] Scheduler used to execute the
        operation. If not specified, defaults to the ImmediateScheduler.

    Returns {Observable} An observable sequence which results from the
    comonadic bind operation.
    """

    scheduler = scheduler or immediate_scheduler
    source = self

    def factory():
        chain = [None]

        def mapper(x):
            curr = ChainObservable(x)

            chain[0] and chain[0].on_next(x)
            chain[0] = curr

            return curr

        def on_error(e):
            if chain[0]:
                chain[0].on_error(e)

        def on_completed():
            if chain[0]:
                chain[0].on_completed()

        return source.map(
            mapper
        ).tap(
            noop, on_error, on_completed
        ).observe_on(
            scheduler
        ).map(
            selector
        )

    return Observable.defer(factory)
