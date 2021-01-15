from enum import Enum

from django.contrib.gis.measure import Area, Distance
from measurement.measures import Volume, Weight


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


DISTANCE_UNITS = Enum(  # type: ignore
    "DistanceUnits", [(unit.upper(), unit) for unit in Distance.UNITS.keys()]
)

AREA_UNITS = Enum(  # type: ignore
    "AreaUnits", [(unit.upper(), unit) for unit in Area.UNITS.keys()]
)
VOLUME_UNITS = Enum(  # type: ignore
    "VolumeUnits", [(unit.upper(), unit) for unit in Volume.UNITS.keys()]
)
WEIGHT_UNITS = Enum(  # type: ignore
    "WeightUnits", [(unit.upper(), unit) for unit in Weight.UNITS.keys()]
)


MEASUREMENT_UNITS = Enum(  # type: ignore
    "MeasurmentUnits",
    [
        (unit.value, unit.value.replace("_", " "))
        for enum in [DISTANCE_UNITS, AREA_UNITS, VOLUME_UNITS, WEIGHT_UNITS]
        for unit in enum
    ],
)
