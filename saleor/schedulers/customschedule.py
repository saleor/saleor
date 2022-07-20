from celery import schedules


class CustomSchedule(schedules.BaseSchedule):
    def __init__(
        self,
        import_path: str,
        schedule: schedules.BaseSchedule,
        nowfun=None,
        app=None,
    ):
        super().__init__(nowfun=nowfun, app=app)
        self.schedule = schedule
        self.import_path = import_path
        if not import_path:
            raise ValueError("Missing import path")

    def remaining_estimate(self, last_run_at):
        return self.schedule.remaining_estimate(last_run_at)

    def is_due(self, last_run_at):
        return self.schedule.is_due(last_run_at)
