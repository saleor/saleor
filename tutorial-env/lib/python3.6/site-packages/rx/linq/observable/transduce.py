"""Transducers for RxPY.

There are several different implementations of transducers in Python.
This implementation is currently targeted for:

 - http://code.sixty-north.com/python-transducers

You should also read the excellent article series "Understanding
Transducers through Python" at:
 - http://sixty-north.com/blog/series/understanding-transducers-through-python

Other implementations of transducers in Python are:

 - https://github.com/cognitect-labs/transducers-python
"""

from rx.core import Observable, AnonymousObservable
from rx.internal import extensionmethod


class Observing(object):

    """An observing transducer."""

    def __init__(self, observer):
        self.observer = observer

    def initial(self):
        return self.observer

    def step(self, obs, input):
        return obs.on_next(input)

    def complete(self, obs):
        return obs.on_completed()

    def __call__(self, result, item):
        return self.step(result, item)


@extensionmethod(Observable)
def transduce(self, transducer):
    """Execute a transducer to transform the observable sequence.

    Keyword arguments:
    :param Transducer transducer: A transducer to execute.

    :returns: An Observable sequence containing the results from the
        transducer.
    :rtype: Observable
    """
    source = self

    def subscribe(observer):
        xform = transducer(Observing(observer))

        def on_next(v):
            try:
                xform.step(observer, v)
            except Exception as e:
                observer.on_error(e)

        def on_completed():
            xform.complete(observer)

        return source.subscribe(on_next, observer.on_error, on_completed)
    return AnonymousObservable(subscribe)
