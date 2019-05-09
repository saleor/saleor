from rx.core import Observable
from rx.internal import extensionmethod


@extensionmethod(Observable, alias="to_iterable")
def to_list(self):
    """Creates a list from an observable sequence.

    Returns an observable sequence containing a single element with a list
    containing all the elements of the source sequence."""

    def accumulator(res, i):
        res = res[:]
        res.append(i)
        return res

    return self.scan(accumulator, seed=[]).start_with([]).last()


@extensionmethod(Observable)
def to_sorted_list(self, key_selector=None, reverse=False):
    """
    Creates a sorted list from an observable sequence,
    with an optional key_selector used to map the attribute for sorting

    Returns an observable sequence containing a single element with a list
    containing all the sorted elements of the source sequence."""

    if key_selector:
        return self.to_list().do_action(on_next=lambda l: l.sort(key=key_selector, reverse=reverse))
    else:
        return self.to_list().do_action(lambda l: l.sort(reverse=reverse))
