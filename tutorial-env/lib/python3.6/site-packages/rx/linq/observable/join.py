import logging
from collections import OrderedDict

from rx import AnonymousObservable, Observable
from rx.internal import noop
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable
from rx.internal import extensionmethod

log = logging.getLogger("Rx")


@extensionmethod(Observable)
def join(self, right, left_duration_selector, right_duration_selector,
         result_selector):
    """Correlates the elements of two sequences based on overlapping
    durations.

    Keyword arguments:
    right -- The right observable sequence to join elements for.
    left_duration_selector -- A function to select the duration (expressed
        as an observable sequence) of each element of the left observable
        sequence, used to determine overlap.
    right_duration_selector -- A function to select the duration (expressed
        as an observable sequence) of each element of the right observable
        sequence, used to determine overlap.
    result_selector -- A function invoked to compute a result element for
        any two overlapping elements of the left and right observable
        sequences. The parameters passed to the function correspond with
        the elements from the left and right source sequences for which
        overlap occurs.

    Return an observable sequence that contains result elements computed
    from source elements that have an overlapping duration.
    """

    left = self

    def subscribe(observer):
        group = CompositeDisposable()
        left_done = [False]
        left_map = OrderedDict()
        left_id = [0]
        right_done = [False]
        right_map = OrderedDict()
        right_id = [0]

        def on_next_left(value):
            duration = None
            current_id = left_id[0]
            left_id[0] += 1
            md = SingleAssignmentDisposable()

            left_map[current_id] = value
            group.add(md)

            def expire():
                if current_id in left_map:
                    del left_map[current_id]
                if not len(left_map) and left_done[0]:
                    observer.on_completed()

                return group.remove(md)

            try:
                duration = left_duration_selector(value)
            except Exception as exception:
                log.error("*** Exception: %s" % exception)
                observer.on_error(exception)
                return

            md.disposable = duration.take(1).subscribe(noop, observer.on_error, lambda: expire())

            for val in right_map.values():
                try:
                    result = result_selector(value, val)
                except Exception as exception:
                    log.error("*** Exception: %s" % exception)
                    observer.on_error(exception)
                    return

                observer.on_next(result)

        def on_completed_left():
            left_done[0] = True
            if right_done[0] or not len(left_map):
                observer.on_completed()

        group.add(left.subscribe(on_next_left, observer.on_error, on_completed_left))

        def on_next_right(value):
            duration = None
            current_id = right_id[0]
            right_id[0] += 1
            md = SingleAssignmentDisposable()
            right_map[current_id] = value
            group.add(md)

            def expire():
                if current_id in right_map:
                    del right_map[current_id]
                if not len(right_map) and right_done[0]:
                    observer.on_completed()

                return group.remove(md)

            try:
                duration = right_duration_selector(value)
            except Exception as exception:
                log.error("*** Exception: %s" % exception)
                observer.on_error(exception)
                return

            md.disposable = duration.take(1).subscribe(noop, observer.on_error, lambda: expire())

            for val in left_map.values():
                try:
                    result = result_selector(val, value)
                except Exception as exception:
                    log.error("*** Exception: %s" % exception)
                    observer.on_error(exception)
                    return

                observer.on_next(result)

        def on_completed_right():
            right_done[0] = True
            if left_done[0] or not len(right_map):
                observer.on_completed()

        group.add(right.subscribe(on_next_right, observer.on_error, on_completed_right))
        return group
    return AnonymousObservable(subscribe)
