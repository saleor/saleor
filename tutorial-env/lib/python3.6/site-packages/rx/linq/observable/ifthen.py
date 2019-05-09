from rx import Observable
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable)
def if_then(cls, condition, then_source, else_source=None, scheduler=None):
    """Determines whether an observable collection contains values.

    Example:
    1 - res = rx.Observable.if(condition, obs1)
    2 - res = rx.Observable.if(condition, obs1, obs2)
    3 - res = rx.Observable.if(condition, obs1, scheduler=scheduler)

    Keyword parameters:
    condition -- {Function} The condition which determines if the
        then_source or else_source will be run.
    then_source -- {Observable} The observable sequence or Promise that
        will be run if the condition function returns true.
    else_source -- {Observable} [Optional] The observable sequence or
        Promise that will be run if the condition function returns False.
        If this is not provided, it defaults to rx.Observable.empty
    scheduler -- [Optional] Scheduler to use.

    Returns an observable {Observable} sequence which is either the
    then_source or else_source.
    """

    else_source = else_source or Observable.empty(scheduler=scheduler)

    then_source = Observable.from_future(then_source)
    else_source = Observable.from_future(else_source)

    def factory():
        return then_source if condition() else else_source
    return Observable.defer(factory)
