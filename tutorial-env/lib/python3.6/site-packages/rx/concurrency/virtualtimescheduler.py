import logging

from rx.internal import PriorityQueue, ArgumentOutOfRangeException

from .schedulerbase import SchedulerBase
from .scheduleditem import ScheduledItem
from .scheduleperiodic import SchedulePeriodic

log = logging.getLogger("Rx")


class VirtualTimeScheduler(SchedulerBase):
    """Virtual Scheduler. This scheduler should work with either
    datetime/timespan or ticks as int/int"""

    def __init__(self, initial_clock=0):
        """Creates a new virtual time scheduler with the specified initial
        clock value and absolute time comparer.

        Keyword arguments:
        initial_clock -- Initial value for the clock.
        comparer -- Comparer to determine causality of events based on absolute
            time.
        """
        self.clock = initial_clock

        self.is_enabled = False
        self.queue = PriorityQueue(1024)

        super(VirtualTimeScheduler, self).__init__()

    @property
    def now(self):
        """Gets the schedulers absolute time clock value as datetime offset."""

        return self.to_datetime(self.clock)

    def schedule(self, action, state=None):
        """Schedules an action to be executed."""

        return self.schedule_absolute(self.clock, action, state)

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime. Return the disposable
        object used to cancel the scheduled action (best effort)

        Keyword arguments:
        duetime -- Relative time after which to execute the action.
        action -- Action to be executed.
        state -- [Optional] State passed to the action to be executed."""

        runat = self.add(self.clock, self.to_relative(duetime))
        return self.schedule_absolute(duetime=runat, action=action, state=state)

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime."""

        si = ScheduledItem(self, state, action, duetime)
        self.queue.enqueue(si)
        return si.disposable

    def schedule_periodic(self, period, action, state=None):
        scheduler = SchedulePeriodic(self, period, action, state)
        return scheduler.start()

    def start(self):
        """Starts the virtual time scheduler."""

        if self.is_enabled:
            return

        self.is_enabled = True
        while self.is_enabled:
            next = self.get_next()
            if not next:
                break
            if next.duetime > self.clock:
                self.clock = next.duetime
            next.invoke()

        self.is_enabled = False

    def stop(self):
        """Stops the virtual time scheduler."""

        self.is_enabled = False

    def advance_to(self, time):
        """Advances the schedulers clock to the specified time, running all
        work til that point.

        Keyword arguments:
        time -- Absolute time to advance the schedulers clock to."""

        if self.clock > time:
            raise ArgumentOutOfRangeException()

        if self.clock == time:
            return

        if self.is_enabled:
            return

        self.is_enabled = True

        while self.is_enabled:
            next = self.get_next()
            if not next:
                break

            if next.duetime > time:
                self.queue.enqueue(next)
                break

            if next.duetime > self.clock:
                self.clock = next.duetime

            next.invoke()

        self.is_enabled = False
        self.clock = time

    def advance_by(self, time):
        """Advances the schedulers clock by the specified relative time,
        running all work scheduled for that timespan.

        Keyword arguments:
        time -- Relative time to advance the schedulers clock by."""

        log.debug("VirtualTimeScheduler.advance_by(time=%s)", time)

        dt = self.add(self.clock, time)
        if self.clock > dt:
            raise ArgumentOutOfRangeException()
        return self.advance_to(dt)

    def sleep(self, time):
        """Advances the schedulers clock by the specified relative time.

        Keyword arguments:
        time -- Relative time to advance the schedulers clock by."""

        dt = self.add(self.clock, time)

        if self.clock > dt:
            raise ArgumentOutOfRangeException()

        self.clock = dt

    def get_next(self):
        """Returns the next scheduled item to be executed."""

        while len(self.queue):
            next = self.queue.dequeue()
            if not next.is_cancelled():
                return next

        return None

    @staticmethod
    def add(absolute, relative):
        raise NotImplementedError
