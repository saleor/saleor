from datetime import timedelta

from rx import AnonymousObservable, Observable
from rx.concurrency import timeout_scheduler
from rx.internal.utils import add_ref
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable, \
    RefCountDisposable, SerialDisposable
from rx.subjects import Subject
from rx.internal import extensionmethod


@extensionmethod(Observable)
def window_with_time(self, timespan, timeshift=None, scheduler=None):
    source = self

    if timeshift is None:
        timeshift = timespan

    if not isinstance(timespan, timedelta):
        timespan = timedelta(milliseconds=timespan)
    if not isinstance(timeshift, timedelta):
        timeshift = timedelta(milliseconds=timeshift)

    scheduler = scheduler or timeout_scheduler

    def subscribe(observer):
        timer_d = SerialDisposable()
        next_shift = [timeshift]
        next_span = [timespan]
        total_time = [timedelta(0)]
        q = []

        group_disposable = CompositeDisposable(timer_d)
        ref_count_disposable = RefCountDisposable(group_disposable)

        def create_timer():
            m = SingleAssignmentDisposable()
            timer_d.disposable = m
            is_span = False
            is_shift = False

            if next_span[0] == next_shift[0]:
                is_span = True
                is_shift = True
            elif next_span[0] < next_shift[0]:
                is_span = True
            else:
                is_shift = True

            new_total_time = next_span[0] if is_span else next_shift[0]

            ts = new_total_time - total_time[0]
            total_time[0] = new_total_time
            if is_span:
                next_span[0] += timeshift

            if is_shift:
                next_shift[0] += timeshift

            def action(scheduler, state=None):
                s = None

                if is_shift:
                    s = Subject()
                    q.append(s)
                    observer.on_next(add_ref(s, ref_count_disposable))

                if is_span:
                    s = q.pop(0)
                    s.on_completed()

                create_timer()
            m.disposable = scheduler.schedule_relative(ts, action)

        q.append(Subject())
        observer.on_next(add_ref(q[0], ref_count_disposable))
        create_timer()

        def on_next(x):
            for s in q:
                s.on_next(x)

        def on_error(e):
            for s in q:
                s.on_error(e)

            observer.on_error(e)

        def on_completed():
            for s in q:
                s.on_completed()

            observer.on_completed()

        group_disposable.add(source.subscribe(on_next, on_error, on_completed))
        return ref_count_disposable
    return AnonymousObservable(subscribe)
