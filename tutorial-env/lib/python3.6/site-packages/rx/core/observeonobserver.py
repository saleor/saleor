from rx.core.scheduledobserver import ScheduledObserver


class ObserveOnObserver(ScheduledObserver):
    def __init__(self, scheduler, observer):
        super(ObserveOnObserver, self).__init__(scheduler, observer)

    def _on_next_core(self, value):
        super(ObserveOnObserver, self)._on_next_core(value)
        self.ensure_active()

    def _on_error_core(self, e):
        super(ObserveOnObserver, self)._on_error_core(e)
        self.ensure_active()

    def _on_completed_core(self):
        super(ObserveOnObserver, self)._on_completed_core()
        self.ensure_active()
