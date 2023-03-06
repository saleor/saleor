import importlib
from typing import Dict

from celery.schedules import BaseSchedule
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.db import models
from django.db.models import signals
from django_celery_beat import models as base_models
from django_celery_beat import querysets

from . import customschedule


class CustomSchedule(models.Model):  # type: ignore[django-manager-missing] # problem with django-stubs # noqa: E501
    """Defines the db model storing the details of a custom Celery beat schedulers.

    This model keeps track of the Python import path of the custom Celery beat scheduler
    (class MyCustomScheduler(celery.schedules.BaseScheduler)).
    Then uses the import path to invoke the custom scheduler when the time is due
    to invoke it.

    Import path should be pointing to the initialized object (variable), like so:
    >>> # ./my_pkg/scheduler.py
    >>> class MyScheduler(BaseSchedule):
    ...     # Do something
    ...     pass
    ...
    >>> my_scheduler = MyScheduler()
    >>> import_path = "my_pkg.scheduler.my_scheduler"
    """

    no_changes = False

    CACHED_SCHEDULES: Dict[str, BaseSchedule] = {}
    schedule_import_path = models.CharField(
        max_length=255,
        help_text="The python import path where the Celery scheduler is defined at",
        unique=True,
    )

    @property
    def schedule(self):
        """Return the custom Celery scheduler from cache or from the import path."""
        obj = self.CACHED_SCHEDULES.get(self.schedule_import_path)
        if obj is None:
            module_path, class_name = self.schedule_import_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            obj = getattr(module, class_name)
            if not isinstance(obj, BaseSchedule):
                raise SuspiciousOperation(
                    f"Expected type of {self.schedule_import_path!r} to be inheriting "
                    f"from BaseScheduler but found: "
                    f"{type(obj)!r} ({obj.__class__.__bases__!r})",
                )
            self.CACHED_SCHEDULES[module_path] = obj
        return obj

    @classmethod
    def from_schedule(cls, schedule: customschedule.CustomSchedule):
        spec = {
            "schedule_import_path": schedule.import_path,
        }
        try:
            return cls.objects.get(**spec)
        except cls.DoesNotExist:
            return cls(**spec)

    def __str__(self):
        return f"{self.schedule_import_path=}"


PeriodicTaskManager = models.Manager.from_queryset(querysets.PeriodicTaskQuerySet)


class CustomPeriodicTask(base_models.PeriodicTask):
    no_changes = False

    custom = models.ForeignKey(
        CustomSchedule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Custom Schedule",
        help_text=(
            "Custom Schedule to run the task on. "
            "Set only one schedule type, leave the others null."
        ),
    )

    objects = PeriodicTaskManager()

    def validate_unique(self, *args, **kwargs):
        models.Model.validate_unique(self, *args, **kwargs)

        # Schedule types list is hard-coded in the super-method
        schedule_types = ["interval", "crontab", "solar", "clocked", "custom"]
        selected_schedule_types = [s for s in schedule_types if getattr(self, s)]

        if len(selected_schedule_types) == 0:
            raise ValidationError(
                "One of clocked, interval, crontab, solar, or custom must be set."
            )

        err_msg = "Only one of clocked, interval, crontab, solar, or custom must be set"
        if len(selected_schedule_types) > 1:
            error_info = {}
            for selected_schedule_type in selected_schedule_types:
                error_info[selected_schedule_type] = [err_msg]
            raise ValidationError(error_info)

        # clocked must be one off task
        if self.clocked and not self.one_off:
            err_msg = "clocked must be one off, one_off must set True"
            raise ValidationError(err_msg)

    @property
    def schedule(self):
        if self.custom:
            return self.custom.schedule
        return super().schedule


# The hooks are needed by django-celery-beat in order to detect other Python modules
# dynamically changing the model data
# CustomPeriodicTask
signals.pre_delete.connect(base_models.PeriodicTasks.changed, sender=CustomPeriodicTask)
signals.pre_save.connect(base_models.PeriodicTasks.changed, sender=CustomPeriodicTask)

# CustomSchedule
signals.pre_delete.connect(base_models.PeriodicTasks.changed, sender=CustomSchedule)
signals.pre_save.connect(base_models.PeriodicTasks.changed, sender=CustomSchedule)
