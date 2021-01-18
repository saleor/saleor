from django.contrib.gis.measure import Area, Distance
from measurement.measures import Mass, Volume


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


def prepare_units_dict(measure, **kwargs):
    """Prepare dict with unit class arguments based on units from providing measure.

    Args:
        measure: measurement class with UNITS class argument
        kwargs: additional arguments that should be attached to the unit dict

    """
    units_dict = {unit.upper(): unit for unit in measure.UNITS.keys()}
    units_dict.update(kwargs)
    units_dict["CHOICES"] = [(v, v) for v in units_dict.values()]
    return units_dict


DistanceUnits = type("DistanceUnits", (object,), prepare_units_dict(Distance))

AreaUnits = type("AreaUnits", (object,), prepare_units_dict(Area))

VolumeUnits = type("VolumeUnits", (object,), prepare_units_dict(Volume))

WeightUnits = type("WeightUnits", (object,), prepare_units_dict(Mass, KG="kg"))


def prepare_all_units_dict():
    measurement_dict = {
        unit.upper(): unit
        for units in [DistanceUnits, AreaUnits, VolumeUnits, WeightUnits]
        for unit, _ in units.CHOICES
    }
    measurement_dict["CHOICES"] = [(v, v) for v in measurement_dict.values()]
    return measurement_dict


MeasurementUnits = type("MeasurementUnits", (object,), prepare_all_units_dict())
