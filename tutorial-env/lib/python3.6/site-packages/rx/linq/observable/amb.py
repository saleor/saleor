from rx.core import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable, SingleAssignmentDisposable
from rx.internal import extensionmethod, extensionclassmethod


@extensionmethod(Observable, instancemethod=True)
def amb(self, right_source):
    """Propagates the observable sequence that reacts first.

    right_source Second observable sequence.

    returns an observable sequence that surfaces either of the given
    sequences, whichever reacted first.
    """

    left_source = self
    right_source = Observable.from_future(right_source)

    def subscribe(observer):
        choice = [None]
        left_choice = 'L'
        right_choice = 'R',
        left_subscription = SingleAssignmentDisposable()
        right_subscription = SingleAssignmentDisposable()

        def choice_left():
            if not choice[0]:
                choice[0] = left_choice
                right_subscription.dispose()

        def choice_right():
            if not choice[0]:
                choice[0] = right_choice
                left_subscription.dispose()

        def on_next_left(value):
            with self.lock:
                choice_left()
            if choice[0] == left_choice:
                observer.on_next(value)

        def on_error_left(err):
            with self.lock:
                choice_left()
            if choice[0] == left_choice:
                observer.on_error(err)

        def on_completed_left():
            with self.lock:
                choice_left()
            if choice[0] == left_choice:
                observer.on_completed()

        ld = left_source.subscribe(on_next_left, on_error_left,
                                   on_completed_left)
        left_subscription.disposable = ld

        def on_next_right(value):
            with self.lock:
                choice_right()
            if choice[0] == right_choice:
                observer.on_next(value)

        def on_error_right(err):
            with self.lock:
                choice_right()
            if choice[0] == right_choice:
                observer.on_error(err)

        def on_completed_right():
            with self.lock:
                choice_right()
            if choice[0] == right_choice:
                observer.on_completed()

        rd = right_source.subscribe(on_next_right, on_error_right,
                                    on_completed_right)
        right_subscription.disposable = rd
        return CompositeDisposable(left_subscription, right_subscription)
    return AnonymousObservable(subscribe)


@extensionclassmethod(Observable)
def amb(cls, *args):
    """Propagates the observable sequence that reacts first.

    E.g. winner = rx.Observable.amb(xs, ys, zs)

    Returns an observable sequence that surfaces any of the given sequences,
    whichever reacted first.
    """

    acc = Observable.never()
    if isinstance(args[0], list):
        items = args[0]
    else:
        items = list(args)

    def func(previous, current):
        return previous.amb(current)

    for item in items:
        acc = func(acc, item)

    return acc
