from rx import Observable
from rx.internal import extensionmethod
from rx.internal.utils import adapt_call


@extensionmethod(Observable)
def partition(self, predicate):
    """Returns two observables which partition the observations of the
    source by the given function. The first will trigger observations for
    those values for which the predicate returns true. The second will
    trigger observations for those values where the predicate returns false.
    The predicate is executed once for each subscribed observer. Both also
    propagate all error observations arising from the source and each
    completes when the source completes.

    Keyword arguments:
    predicate -- The function to determine which output Observable will
        trigger a particular observation.

    Returns a list of observables. The first triggers when the predicate
    returns True, and the second triggers when the predicate returns False.
    """

    published = self.publish().ref_count()
    return [
        published.filter(predicate), # where does adapt_call itself
        published.filter(lambda x, i: not adapt_call(predicate)(x, i))
    ]

