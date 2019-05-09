from rx.core import ObservableBase, Observable, AnonymousObservable
from rx.internal import extensionmethod
from rx.subjects import Subject
from rx.disposables import CompositeDisposable


def combine_latest_source(source, subject, result_selector):
    def subscribe(observer):
        has_value = [False, False]
        has_value_all = [False]
        values = [None, None]
        is_done = [False]
        err = [None]

        def next(x, i):
            has_value[i] = True
            values[i] = x

            has_value_all[0] = has_value_all[0] or all(has_value)
            if has_value_all[0]:
                if err[0]:
                    observer.on_error(err[0])
                    return

                try:
                    res = result_selector(*values)
                except Exception as ex:
                    observer.on_error(ex)
                    return
                observer.on_next(res)
            if is_done[0] and values[1]:
                observer.on_completed()

        def on_error_source(e):
            if values[1]:
                observer.on_error(e)
            else:
                err[0] = e

        def on_completed_source():
            is_done[0] = True
            if values[1]:
                observer.on_completed()

        def on_completed_subject():
            is_done[0] = True
            next(True, 1)

        return CompositeDisposable(
            source.subscribe(lambda x: next(x, 0), on_error_source, on_completed_source),
            subject.subscribe(lambda x: next(x, 1), observer.on_error, on_completed_subject)
        )
    return AnonymousObservable(subscribe)


class PausableBufferedObservable(ObservableBase):

    def __init__(self, source, pauser=None):
        self.source = source
        self.controller = Subject()

        if pauser and hasattr(pauser, "subscribe"):
            self.pauser = self.controller.merge(pauser)
        else:
            self.pauser = self.controller

        super(PausableBufferedObservable, self).__init__()

    def _subscribe_core(self, observer):
        previous_should_fire = [None]
        queue = []

        def result_selector(data, should_fire=False):
            return {"data": data, "should_fire": should_fire}

        def on_next(results):
            should_fire = results.get("should_fire")
            if (not previous_should_fire[0] is None) and should_fire != previous_should_fire[0]:
                previous_should_fire[0] = should_fire
                # change in shouldFire
                if should_fire:
                    while len(queue):
                        b = queue.pop(0)
                        observer.on_next(b)
            else:
                previous_should_fire[0] = should_fire
                # new data
                if should_fire:
                    observer.on_next(results["data"])
                else:
                    queue.append(results["data"])

        def on_error(err):
            # Empty buffer before sending error
            while len(queue):
                observer.on_next(queue.pop(0))
            observer.on_error(err)

        def on_completed():
            # Empty buffer before sending completion
            while len(queue):
                observer.on_next(queue.pop(0))
            observer.on_completed()

        subscription = combine_latest_source(
            self.source,
            self.pauser.distinct_until_changed().start_with(False),
            result_selector
        ).subscribe(on_next, on_error, on_completed)

        return subscription

    def pause(self):
        self.controller.on_next(False)

    def resume(self):
        self.controller.on_next(True)


@extensionmethod(Observable)
def pausable_buffered(self, subject):
    """Pauses the underlying observable sequence based upon the observable
    sequence which yields True/False, and yields the values that were
    buffered while paused.

    Example:
    pauser = rx.Subject()
    source = rx.Observable.interval(100).pausable_buffered(pauser)

    Keyword arguments:
    pauser -- {Observable} The observable sequence used to pause the
        underlying sequence.

    Returns the observable {Observable} sequence which is paused based upon
    the pauser."""

    return PausableBufferedObservable(self, subject)
