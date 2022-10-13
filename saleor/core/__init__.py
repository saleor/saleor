default_app_config = "saleor.core.app.CoreAppConfig"


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
