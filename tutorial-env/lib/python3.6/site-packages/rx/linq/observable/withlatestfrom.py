from rx.core import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable, SingleAssignmentDisposable
from rx.internal import extensionmethod, extensionclassmethod


def listify_args(*a):
    return list(a)


@extensionmethod(Observable, instancemethod=True)
def with_latest_from(self, *args):
    """Merges the specified observable sequences into one observable sequence
    by using the selector function only when the source observable sequence
    (the instance) produces an element. The other observables can be passed
    either as seperate arguments or as a list.

    1 - obs = observable.with_latest_from(obs1, obs2, obs3,
                                        lambda o1, o2, o3: o1 + o2 + o3)
    2 - obs = observable.with_latest_from([obs1, obs2, obs3],
                                        lambda o1, o2, o3: o1 + o2 + o3)

    Returns an observable sequence containing the result of combining
    elements of the sources using the specified result selector function.
    """

    if args and isinstance(args[0], list):
        children = args[0]
        result_selector = args[1]
        args_ = [self] + children + [result_selector]
    else:
        args_ = [self] + list(args)

    return Observable.with_latest_from(*args_)


@extensionclassmethod(Observable)
def with_latest_from(cls, *args):

    """Merges the specified observable sequences into one observable sequence
    by using the selector function only when the first observable sequence
    produces an element. The observables can be passed either as seperate
    arguments or as a list.

    1 - obs = Observable.with_latest_from(obs1, obs2, obs3,
                                       lambda o1, o2, o3: o1 + o2 + o3)
    2 - obs = Observable.with_latest_from([obs1, obs2, obs3],
                                        lambda o1, o2, o3: o1 + o2 + o3)

    Returns an observable sequence containing the result of combining
    elements of the sources using the specified result selector function.
    """

    if args and isinstance(args[0], list):
        observables = args[0]
        result_selector = args[1]
    else:
        observables = list(args[:-1])
        result_selector = args[-1]

    NO_VALUE = object()

    def subscribe(observer):

        def subscribe_all(parent, *children):

            values = [NO_VALUE for _ in children]

            def subscribe_child(i, child):
                subscription = SingleAssignmentDisposable()
                def on_next(value):
                    with parent.lock:
                        values[i] = value
                subscription.disposable = child.subscribe(
                    on_next, observer.on_error)
                return subscription

            parent_subscription = SingleAssignmentDisposable()
            def on_next(value):
                with parent.lock:
                    if NO_VALUE not in values:
                        try:
                            result = result_selector(value, *values)
                        except Exception as error:
                            observer.on_error(error)
                        else:
                            observer.on_next(result)
            parent_subscription.disposable = parent.subscribe(
                on_next, observer.on_error, observer.on_completed)

            return listify_args(
                parent_subscription,
                *(subscribe_child(*a) for a in enumerate(children))
            )

        return CompositeDisposable(subscribe_all(*observables))
    return AnonymousObservable(subscribe)
