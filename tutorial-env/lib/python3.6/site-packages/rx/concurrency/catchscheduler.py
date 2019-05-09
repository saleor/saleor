from rx.core import Disposable
from rx.disposables import SingleAssignmentDisposable

from .schedulerbase import SchedulerBase


class CatchScheduler(SchedulerBase):
    def __init__(self, scheduler, handler):
        """Create new CatchScheduler.

        Returns a scheduler that wraps the original scheduler, adding
        exception handling for scheduled actions.
        """
        self._scheduler = scheduler
        self._handler = handler
        self._recursive_original = None
        self._recursive_wrapper = None

        super(CatchScheduler, self).__init__()

    def local_now(self):
        return self._scheduler.now

    def schedule_now(self, state, action):
        """Schedules an action to be executed."""

        return self._scheduler.scheduleWithState(state, self._wrap(action))

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed after duetime."""

        return self._scheduler.schedule_relative(duetime, self._wrap(action), state=state)

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime."""

        return self._scheduler.schedule_absolute(duetime, self._wrap(action), state=state)

    def _clone(self, scheduler):
        return CatchScheduler(scheduler, self._handler)

    def _wrap(self, action):
        parent = self

        def wrapped_action(self, state):
            try:
                return action(parent._get_recursive_wrapper(self), state)
            except Exception as ex:
                if not parent._handler(ex):
                    raise Exception(ex)
                return Disposable.empty()
        return wrapped_action

    def _get_recursive_wrapper(self, scheduler):
        if self._recursive_original != scheduler:
            self._recursive_original = scheduler
            wrapper = self._clone(scheduler)
            wrapper._recursive_original = scheduler
            wrapper._recursive_wrapper = wrapper
            self._recursive_wrapper = wrapper

        return self._recursive_wrapper

    def schedule_periodic(self, period, action, state=None):
        d = SingleAssignmentDisposable()
        failed = [False]

        def periodic_action(periodic_state):
            if failed[0]:
                return None
            try:
                return action(periodic_state)
            except Exception as ex:
                failed[0] = True
                if not self._handler(ex):
                    raise Exception(ex)
                d.dispose()
                return None

        d.disposable = self._scheduler.schedule_periodic(periodic_action, period, state)
        return d
