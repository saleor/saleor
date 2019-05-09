from measurement.base import BidimensionalMeasure


from measurement.measures.distance import Distance
from measurement.measures.time import Time


__all__ = [
    'Speed'
]


class Speed(BidimensionalMeasure):
    PRIMARY_DIMENSION = Distance
    REFERENCE_DIMENSION = Time

    ALIAS = {
        'mph': 'mi__hr',
        'kph': 'km__hr',
    }
