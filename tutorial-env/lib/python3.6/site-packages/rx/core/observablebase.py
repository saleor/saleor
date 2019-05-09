import types
from abc import abstractmethod

from rx import config
from rx.concurrency import current_thread_scheduler

from . import Observer, Observable, Disposable
from .anonymousobserver import AnonymousObserver
from .autodetachobserver import AutoDetachObserver


class ObservableBase(Observable):
    """Represents a push-style collection."""

    def __init__(self):
        self.lock = config["concurrency"].RLock()

        # Deferred instance method assignment
        for name, method in self._methods:
            setattr(self, name, types.MethodType(method, self))

    def subscribe(self, on_next=None, on_error=None, on_completed=None, observer=None):
        """Subscribe an observer to the observable sequence.

        Examples:
        1 - source.subscribe()
        2 - source.subscribe(observer)
        3 - source.subscribe(on_next)
        4 - source.subscribe(on_next, on_error)
        5 - source.subscribe(on_next, on_error, on_completed)

        Keyword arguments:
        on_next -- [Optional] Action to invoke for each element in the
            observable sequence.
        on_error -- [Optional] Action to invoke upon exceptional
            termination of the observable sequence.
        on_completed -- [Optional] Action to invoke upon graceful
            termination of the observable sequence.
        observer -- [Optional] The object that is to receive
            notifications. You may subscribe using an observer or
            callbacks, not both.

        Return disposable object representing an observer's subscription
            to the observable sequence.
        """
        # Accept observer as first parameter
        if isinstance(on_next, Observer):
            observer = on_next
        elif hasattr(on_next, "on_next") and callable(on_next.on_next):
            observer = on_next
        elif not observer:
            observer = AnonymousObserver(on_next, on_error, on_completed)

        auto_detach_observer = AutoDetachObserver(observer)

        def fix_subscriber(subscriber):
            """Fixes subscriber to make sure it returns a Disposable instead
            of None or a dispose function"""

            if not hasattr(subscriber, "dispose"):
                subscriber = Disposable.create(subscriber)

            return subscriber

        def set_disposable(scheduler=None, value=None):
            try:
                subscriber = self._subscribe_core(auto_detach_observer)
            except Exception as ex:
                if not auto_detach_observer.fail(ex):
                    raise
            else:
                auto_detach_observer.disposable = fix_subscriber(subscriber)

        # Subscribe needs to set up the trampoline before for subscribing.
        # Actually, the first call to Subscribe creates the trampoline so
        # that it may assign its disposable before any observer executes
        # OnNext over the CurrentThreadScheduler. This enables single-
        # threaded cancellation
        # https://social.msdn.microsoft.com/Forums/en-US/eb82f593-9684-4e27-
        # 97b9-8b8886da5c33/whats-the-rationale-behind-how-currentthreadsche
        # dulerschedulerequired-behaves?forum=rx
        if current_thread_scheduler.schedule_required():
            current_thread_scheduler.schedule(set_disposable)
        else:
            set_disposable()

        # Hide the identity of the auto detach observer
        return Disposable.create(auto_detach_observer.dispose)

    @abstractmethod
    def _subscribe_core(self, observer):
        return NotImplemented
