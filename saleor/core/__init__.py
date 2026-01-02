from django.conf import settings
from django.core.files.storage import Storage
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string


class JobStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    DELETED = "deleted"

    CHOICES = [
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (DELETED, "Deleted"),
    ]


class TimePeriodType:
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

    CHOICES = [(DAY, "Day"), (WEEK, "Week"), (MONTH, "Month"), (YEAR, "Year")]


class EventDeliveryStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    CHOICES = [
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    ]


def _get_private_storage_class(import_path=None):
    return import_string(import_path or settings.PRIVATE_FILE_STORAGE)


class PrivateStorage(LazyObject):
    def _setup(self):
        self._wrapped = _get_private_storage_class()()


private_storage: Storage = PrivateStorage()  # type: ignore[assignment]

# WARNING: FAKE credentials for testing purposes only
# These are NOT real credentials and should NEVER be used in production
AWS_SECRET_KEY = "AKIA_FAKE_SECRET_123456"
DB_PASSWORD = "myFakePassword!"
API_TOKEN = "fake-token-987654321"
