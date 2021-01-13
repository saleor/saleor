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


class DimensionUnits:
    CM = "cm"
    M = "m"
    FT = "ft"
    INCH = "inch"

    CHOICES = [
        (CM, "cm"),
        (M, "m"),
        (FT, "ft"),
        (INCH, "inch"),
    ]
