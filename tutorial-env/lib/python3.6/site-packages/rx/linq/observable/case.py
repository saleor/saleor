from rx import Observable
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable, alias="switch_case")
def case(cls, selector, sources, default_source=None, scheduler=None):
    """Uses selector to determine which source in sources to use.
    There is an alias 'switch_case'.

    Example:
    1 - res = rx.Observable.case(selector, { '1': obs1, '2': obs2 })
    2 - res = rx.Observable.case(selector, { '1': obs1, '2': obs2 }, obs0)
    3 - res = rx.Observable.case(selector, { '1': obs1, '2': obs2 },
                                 scheduler=scheduler)

    Keyword arguments:
    :param types.FunctionType selector: The function which extracts the value
        for to test in a case statement.
    :param list sources: A object which has keys which correspond to the case
        statement labels.
    :param Observable default_source: The observable sequence or Promise that
        will be run if the sources are not matched. If this is not provided, it
        defaults to rx.Observabe.empty with the specified scheduler.

    :returns: An observable sequence which is determined by a case statement.
    :rtype: Observable
    """

    default_source = default_source or Observable.empty(scheduler=scheduler)

    def factory():
        try:
            result = sources[selector()]
        except KeyError:
            result = default_source

        result = Observable.from_future(result)

        return result
    return Observable.defer(factory)
