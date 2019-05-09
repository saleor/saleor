from measurement.base import BidimensionalMeasure


def get_measurement(measure, value, unit=None, original_unit=None):
    unit = unit or measure.STANDARD_UNIT

    m = measure(
        **{unit: value}
    )
    if original_unit:
        m.unit = original_unit
    if isinstance(m, BidimensionalMeasure):
        m.reference.value = 1
    return m
