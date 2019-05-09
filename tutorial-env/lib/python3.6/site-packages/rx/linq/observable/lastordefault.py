from rx import Observable, AnonymousObservable
from rx.internal.exceptions import SequenceContainsNoElementsError
from rx.internal import extensionmethod


def last_or_default_async(source, has_default=False, default_value=None):
    def subscribe(observer):
        value = [default_value]
        seen_value = [False]

        def on_next(x):
            value[0] = x
            seen_value[0] = True

        def on_completed():
            if not seen_value[0] and not has_default:
                observer.on_error(SequenceContainsNoElementsError())
            else:
                observer.on_next(value[0])
                observer.on_completed()

        return source.subscribe(on_next, observer.on_error, on_completed)
    return AnonymousObservable(subscribe)


@extensionmethod(Observable)
def last_or_default(self, predicate=None, default_value=None):
    """Return last or default element.

    Returns the last element of an observable sequence that satisfies
    the condition in the predicate, or a default value if no such
    element exists.

    Examples:
    res = source.last_or_default()
    res = source.last_or_default(lambda x: x > 3)
    res = source.last_or_default(lambda x: x > 3, 0)
    res = source.last_or_default(None, 0)

    predicate -- {Function} [Optional] A predicate function to evaluate
        for elements in the source sequence.
    default_value -- [Optional] The default value if no such element
        exists. If not specified, defaults to None.

    Returns {Observable} Sequence containing the last element in the
    observable sequence that satisfies the condition in the predicate,
    or a default value if no such element exists.
    """
    if predicate:
        return self.filter(predicate).last_or_default(None, default_value)

    return last_or_default_async(self, True, default_value)
