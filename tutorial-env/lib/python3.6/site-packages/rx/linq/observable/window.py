import logging

from rx import AnonymousObservable, Observable
from rx.internal.utils import add_ref
from rx.internal import noop
from rx.disposables import SingleAssignmentDisposable, SerialDisposable, \
    CompositeDisposable, RefCountDisposable
from rx.subjects import Subject
from rx.internal import extensionmethod

log = logging.getLogger("Rx")


@extensionmethod(Observable)
def window(self, window_openings=None, window_closing_selector=None):
    """Projects each element of an observable sequence into zero or more
    windows.

    Keyword arguments:
    :param Observable window_openings: Observable sequence whose elements
        denote the creation of windows.
    :param types.FunctionType window_closing_selector: [Optional] A function
        invoked to define the closing of each produced window. It defines the
        boundaries of the produced windows (a window is started when the
        previous one is closed, resulting in non-overlapping windows).

    :returns: An observable sequence of windows.
    :rtype: Observable[Observable]
    """

    # Make it possible to call window with a single unnamed parameter
    if not isinstance(window_openings, Observable) and callable(window_openings):
        window_closing_selector = window_openings
        window_openings = None

    if window_openings and not window_closing_selector:
        return observable_window_with_bounaries(self, window_openings)

    if not window_openings and window_closing_selector:
        return observable_window_with_closing_selector(self, window_closing_selector)

    return observable_window_with_openings(self, window_openings, window_closing_selector)

def observable_window_with_openings(self, window_openings, window_closing_selector):
    return window_openings.group_join(self, window_closing_selector, lambda _: Observable.empty(), lambda _, window: window)

def observable_window_with_bounaries(self, window_boundaries):
    source = self

    def subscribe(observer):
        window = [Subject()]
        d = CompositeDisposable()
        r = RefCountDisposable(d)

        observer.on_next(add_ref(window[0], r))

        def on_next_window(x):
            window[0].on_next(x)

        def on_error(err):
            window[0].on_error(err)
            observer.on_error(err)

        def on_completed():
            window[0].on_completed()
            observer.on_completed()

        d.add(source.subscribe(on_next_window, on_error, on_completed))

        def on_next_observer(w):
            window[0].on_completed()
            window[0] = Subject()
            observer.on_next(add_ref(window[0], r))

        d.add(window_boundaries.subscribe(on_next_observer, on_error, on_completed))
        return r
    return AnonymousObservable(subscribe)

def observable_window_with_closing_selector(self, window_closing_selector):
    source = self

    def subscribe(observer):
        m = SerialDisposable()
        d = CompositeDisposable(m)
        r = RefCountDisposable(d)
        window = [Subject()]

        observer.on_next(add_ref(window[0], r))

        def on_next(x):
            window[0].on_next(x)

        def on_error(ex):
            window[0].on_error(ex)
            observer.on_error(ex)

        def on_completed():
            window[0].on_completed()
            observer.on_completed()

        d.add(source.subscribe(on_next, on_error, on_completed))

        def create_window_close():
            try:
                window_close = window_closing_selector()
            except Exception as exception:
                log.error("*** Exception: %s" % exception)
                observer.on_error(exception)
                return

            def on_completed():
                window[0].on_completed()
                window[0] = Subject()
                observer.on_next(add_ref(window[0], r))
                create_window_close()

            m1 = SingleAssignmentDisposable()
            m.disposable = m1
            m1.disposable = window_close.take(1).subscribe(noop, on_error, on_completed)

        create_window_close()
        return r
    return AnonymousObservable(subscribe)
