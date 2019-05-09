import re

from rx.core import AnonymousObservable, Observable
from rx.core.blockingobservable import BlockingObservable
from rx.concurrency import new_thread_scheduler
from rx.internal import extensionmethod, extensionclassmethod
from rx import config

from .coldobservable import ColdObservable
from .reactivetest import ReactiveTest

on_next = ReactiveTest.on_next
on_completed = ReactiveTest.on_completed
on_error = ReactiveTest.on_error

_pattern = r"\(?([a-zA-Z0-9]+)\)?|(-|[xX]|\|)"
_tokens = re.compile(_pattern)


@extensionclassmethod(Observable, alias="from_string")
def from_marbles(cls, string, scheduler=None):
    """Convert a marble diagram string to an observable sequence, using
    an optional scheduler to enumerate the events.

    Special characters:
    - = Timespan of 100 ms
    x = on_error()
    | = on_completed()

    All other characters are treated as an on_next() event at the given
    moment they are found on the string.

    Examples:
    1 - res = rx.Observable.from_string("1-2-3-|")
    2 - res = rx.Observable.from_string("1-(42)-3-|")
    3 - res = rx.Observable.from_string("1-2-3-x", rx.Scheduler.timeout)

    Keyword arguments:
    string -- String with marble diagram
    scheduler -- [Optional] Scheduler to run the the input sequence on.

    Returns the observable sequence whose elements are pulled from the
    given marble diagram string.
    """

    scheduler = scheduler or new_thread_scheduler

    completed = [False]
    messages = []
    timespan = [0]

    def handle_timespan(value):
        timespan[0] += 100

    def handle_on_next(value):
        timespan[0] += 10
        if value in ('T', 'F'):
            value = True if value == 'T' else False
        messages.append(on_next(timespan[0], value))


    def handle_on_completed(value):
        timespan[0] += 10
        messages.append(on_completed(timespan[0]))
        completed[0] = True

    def handle_on_error(value):
        timespan[0] += 10
        messages.append(on_error(timespan[0], value))
        completed[0] = True

    specials = {
        '-': handle_timespan,
        'x': handle_on_error,
        'X': handle_on_error,
        '|': handle_on_completed
    }

    for groups in _tokens.findall(string):
        for token in groups:
            if token:
                func = specials.get(token, handle_on_next)
                func(token)

    if not completed[0]:
        messages.append(on_completed(timespan[0]))

    return ColdObservable(scheduler, messages)


@extensionmethod(Observable, alias="to_string")
def to_marbles(self, scheduler=None):
    """Convert an observable sequence into a marble diagram string

    Keyword arguments:
    scheduler -- [Optional] The scheduler used to run the the input
        sequence on.

    Returns Observable
    """
    scheduler = scheduler or new_thread_scheduler
    source = self

    def subscribe(observer):
        result = []
        previously = [scheduler.now]

        def add_timespan():
            now = scheduler.now
            diff = now - previously[0]
            previously[0] = now
            msecs = scheduler.to_relative(diff)
            dashes = "-" * int((msecs + 50) / 100)
            result.append(dashes)

        def on_next(value):
            add_timespan()
            result.append(stringify(value))

        def on_error(exception):
            add_timespan()
            result.append(stringify(exception))
            observer.on_next("".join(n for n in result))
            observer.on_completed()

        def on_completed():
            add_timespan()
            result.append("|")
            observer.on_next("".join(n for n in result))
            observer.on_completed()

        return source.subscribe(on_next, on_error, on_completed)
    return AnonymousObservable(subscribe)


@extensionmethod(BlockingObservable, alias="to_string")  # noqa
def to_marbles(self, scheduler=None):
    """Convert an observable sequence into a marble diagram string

    Keyword arguments:
    scheduler -- [Optional] The scheduler used to run the the input
        sequence on.

    Returns marble string.
    """

    latch = config["concurrency"].Event()
    ret = [None]

    def on_next(value):
        ret[0] = value

    self.observable.to_marbles(scheduler=scheduler).subscribe(on_next, on_completed=latch.set)

    # Block until the subscription completes and then return
    latch.wait()

    return ret[0]


def stringify(value):
    """Utility for stringifying an event.
    """
    string = str(value)
    if len(string) > 1:
        string = "(%s)" % string

    return string
