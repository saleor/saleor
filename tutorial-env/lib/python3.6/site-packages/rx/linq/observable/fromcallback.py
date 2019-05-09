from rx.core import Observable, AnonymousObservable
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable)
def from_callback(cls, func, selector=None):
    """Converts a callback function to an observable sequence.

    Keyword arguments:
    func -- {Function} Function with a callback as the last parameter to
        convert to an Observable sequence.
    selector -- {Function} [Optional] A selector which takes the arguments
        from the callback to produce a single item to yield on next.

    Returns {Function} A function, when executed with the required
    parameters minus the callback, produces an Observable sequence with a
    single value of the arguments to the callback as a list.
    """

    def function(*args):
        arguments = list(args)

        def subscribe(observer):
            def handler(*args):
                results = list(args)
                if selector:
                    try:
                        results = selector(args)
                    except Exception as err:
                        observer.on_error(err)
                        return

                    observer.on_next(results)
                else:
                    if isinstance(results, list) and len(results) <= 1:
                        observer.on_next(*results)
                    else:
                        observer.on_next(results)

                    observer.on_completed()

            arguments.append(handler)
            func(*arguments)

        return AnonymousObservable(subscribe)
    return function
