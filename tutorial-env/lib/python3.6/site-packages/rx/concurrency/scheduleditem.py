from rx.disposables import SingleAssignmentDisposable


def default_sub_comparer(x, y):
    return 0 if x == y else 1 if x > y else -1


class ScheduledItem(object):
    def __init__(self, scheduler, state, action, duetime):
        self.scheduler = scheduler
        self.state = state
        self.action = action
        self.duetime = duetime
        self.disposable = SingleAssignmentDisposable()

    def invoke(self):
        ret = self.scheduler.invoke_action(self.action, self.state)
        self.disposable.disposable = ret

    def cancel(self):
        """Cancels the work item by disposing the resource returned by
        invoke_core as soon as possible."""

        self.disposable.dispose()

    def is_cancelled(self):
        return self.disposable.is_disposed

    def __lt__(self, other):
        return self.duetime < other.duetime

    def __gt__(self, other):
        return self.duetime > other.duetime

    def __eq__(self, other):
        return self.duetime == other.duetime
