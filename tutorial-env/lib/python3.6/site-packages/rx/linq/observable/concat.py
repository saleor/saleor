from rx.core import Observable, AnonymousObservable, Disposable
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable, SerialDisposable
from rx.concurrency import CurrentThreadScheduler
from rx.internal import extensionmethod, extensionclassmethod
from rx.internal import Enumerable


@extensionmethod(Observable, instancemethod=True)
def concat(self, *args):
    """Concatenates all the observable sequences. This takes in either an
    array or variable arguments to concatenate.

    1 - concatenated = xs.concat(ys, zs)
    2 - concatenated = xs.concat([ys, zs])

    Returns an observable sequence that contains the elements of each given
    sequence, in sequential order.
    """
    if isinstance(args[0], list):
        items = args[0]
    else:
        items = list(args)

    items.insert(0, self)
    return Observable.concat(items)


@extensionmethod(Observable, instancemethod=True)
def concat_map(self, selector):
    """Maps each emission to an Observable and fires its emissions.
    It will only fire each resulting Observable sequentially.
    The next derived Observable will not start its emissions until the current one calls on_complate
    """
    return self.map(selector).concat_all()


@extensionmethod(Observable)
def __add__(self, other):
    """Pythonic version of concat

    Example:
    zs = xs + ys
    Returns self.concat(other)"""

    return self.concat(other)


@extensionmethod(Observable)
def __iadd__(self, other):
    """Pythonic use of concat

    Example:
    xs += ys

    Returns self.concat(self, other)"""

    return self.concat(self, other)


@extensionclassmethod(Observable)
def concat(cls, *args):
    """Concatenates all the observable sequences.

    1 - res = Observable.concat(xs, ys, zs)
    2 - res = Observable.concat([xs, ys, zs])

    Returns an observable sequence that contains the elements of each given
    sequence, in sequential order.
    """

    scheduler = CurrentThreadScheduler()

    if isinstance(args[0], list) or isinstance(args[0], Enumerable):
        sources = args[0]
    else:
        sources = list(args)

    def subscribe(observer):
        subscription = SerialDisposable()
        cancelable = SerialDisposable()
        enum = iter(sources)
        is_disposed = []

        def action(action1, state=None):
            if is_disposed:
                return

            def on_completed():
                cancelable.disposable = scheduler.schedule(action)

            try:
                current = next(enum)
            except StopIteration:
                observer.on_completed()
            except Exception as ex:
                observer.on_error(ex)
            else:
                d = SingleAssignmentDisposable()
                subscription.disposable = d
                d.disposable = current.subscribe(observer.on_next, observer.on_error, on_completed)

        cancelable.disposable = scheduler.schedule(action)

        def dispose():
            is_disposed.append(True)

        return CompositeDisposable(subscription, cancelable, Disposable.create(dispose))

    return AnonymousObservable(subscribe)


@extensionmethod(Observable)
def concat_all(self):
    """Concatenates an observable sequence of observable sequences.

    Returns an observable sequence that contains the elements of each
    observed inner sequence, in sequential order.
    """

    return self.merge(1)
