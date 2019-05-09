import sys

from rx import AnonymousObservable
from rx.disposables import CompositeDisposable

from .exceptions import DisposedException


def add_ref(xs, r):
    def subscribe(observer):
        return CompositeDisposable(r.disposable, xs.subscribe(observer))

    return AnonymousObservable(subscribe)


def adapt_call(func):
    """Adapt called func.

    Adapt call from taking n params to only taking 1 or 2 params
    """

    def _should_reraise_TypeError():
        """Determine whether or not we should re-raise a given TypeError. Since
        we rely on excepting TypeError in order to determine whether or not we
        can adapt a function, we can't immediately determine whether a given
        TypeError is from the adapted function's logic (and should be
        re-raised) or from argspec mismatches (which should not be re-raised).

        Given that this function is private to adapt_call, we know that there will
        always be at least two frames in the given traceback:

        - frame: (func1 | func2) call
            - frame: func call
                - frame: (Optional) TypeError in body

        and hence we can check for the presence of the third frame, which indicates
        whether an error occurred in the body.
        """
        _, __, tb = sys.exc_info()

        return tb.tb_next.tb_next is not None

    cached = [None]

    def func1(arg1, *_, **__):
        return func(arg1)

    def func2(arg1, arg2=None, *_, **__):
        return func(arg1, arg2)

    def func_wrapped(*args, **kw):
        if cached[0]:
            return cached[0](*args, **kw)

        for fn in (func1, func2):
            try:
                ret = fn(*args, **kw)
            except TypeError:
                # Preserve the original traceback if there was a TypeError raised
                # in the body of the adapted function.
                if _should_reraise_TypeError():
                    raise
                else:
                    continue
            else:
                cached[0] = fn
                return ret
        else:
            # We were unable to call the function successfully.
            raise TypeError("Couldn't adapt function {}".format(func.__name__))

    return func_wrapped


def check_disposed(this):
    if this.is_disposed:
        raise DisposedException()


def is_future(p):
    return callable(getattr(p, "add_done_callback", None))


class TimeInterval(object):

    def __init__(self, value, interval):
        self.value = value
        self.interval = interval


class Timestamp(object):

    def __init__(self, value, timestamp):
        self.value = value
        self.timestamp = timestamp
