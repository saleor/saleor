from rx.core import Observable
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable)
def start_async(cls, function_async):
    """Invokes the asynchronous function, surfacing the result through an
    observable sequence.

    Keyword arguments:
    :param types.FunctionType function_async: Asynchronous function which
        returns a Future to run.

    :returns: An observable sequence exposing the function's result value, or an
        exception.
    :rtype: Observable
    """

    try:
        future = function_async()
    except Exception as ex:
        return Observable.throw(ex)

    return Observable.from_future(future)
