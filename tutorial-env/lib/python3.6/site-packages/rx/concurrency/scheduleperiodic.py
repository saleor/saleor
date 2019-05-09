from rx.disposables import SerialDisposable


class SchedulePeriodic(object):
    """Scheduler with support for running periodic tasks. This type of
    scheduler can be used to run timers more efficiently instead of using
    recursive scheduling."""

    def __init__(self, scheduler, period, action, state=None):
        """
        Keyword arguments:
        state -- Initial state passed to the action upon the first iteration.
        period -- Period for running the work periodically.
        action -- Action to be executed, potentially updating the state."""

        self._scheduler = scheduler
        self._state = state
        self._period = period
        self._action = action
        self._cancel = SerialDisposable()

    def tick(self, scheduler, command):
        self._cancel.disposable = self._scheduler.schedule_relative(self._period, self.tick, 0)
        try:
            new_state = self._action(self._state)
        except Exception:
            self._cancel.dispose()
            raise
        else:
            if new_state is not None:  # Update state if other than None
                self._state = new_state

    def start(self):
        """Returns the disposable object used to cancel the scheduled recurring
        action (best effort).
        """

        self._cancel.disposable = self._scheduler.schedule_relative(self._period, self.tick, 0)
        return self._cancel
