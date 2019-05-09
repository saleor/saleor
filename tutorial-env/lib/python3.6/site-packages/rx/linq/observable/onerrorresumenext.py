from rx.core import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable, SingleAssignmentDisposable, \
    SerialDisposable
from rx.concurrency import current_thread_scheduler
from rx.internal import extensionmethod, extensionclassmethod


@extensionmethod(Observable, instancemethod=True)
def on_error_resume_next(self, second):
    """Continues an observable sequence that is terminated normally or by
    an exception with the next observable sequence.

    Keyword arguments:
    second -- Second observable sequence used to produce results after the
        first sequence terminates.

    Returns an observable sequence that concatenates the first and second
    sequence, even if the first sequence terminates exceptionally.
    """

    if not second:
        raise Exception('Second observable is required')

    return Observable.on_error_resume_next([self, second])

@extensionclassmethod(Observable)
def on_error_resume_next(cls, *args):
    """Continues an observable sequence that is terminated normally or by
    an exception with the next observable sequence.

    1 - res = Observable.on_error_resume_next(xs, ys, zs)
    2 - res = Observable.on_error_resume_next([xs, ys, zs])

    Returns an observable sequence that concatenates the source sequences,
    even if a sequence terminates exceptionally.
    """
    # curently not in:
    # 3 - res = Observable.on_error_resume_next(xs, factory)

    scheduler = current_thread_scheduler

    if args and isinstance(args[0], list):
        sources = iter(args[0])
    else:
        sources = iter(args)

    def subscribe(observer):
        subscription = SerialDisposable()
        cancelable = SerialDisposable()

        def action(scheduler, state=None):
            try:
                source = next(sources)
            except StopIteration:
                observer.on_completed()
                return

            # Allow source to be a factory method taking an error
            source = source(state) if callable(source) else source
            current = Observable.from_future(source)

            d = SingleAssignmentDisposable()
            subscription.disposable = d

            def on_resume(state=None):
                scheduler.schedule(action, state)

            d.disposable = current.subscribe(observer.on_next, on_resume, on_resume)

        cancelable.disposable = scheduler.schedule(action)
        return CompositeDisposable(subscription, cancelable)
    return AnonymousObservable(subscribe)
