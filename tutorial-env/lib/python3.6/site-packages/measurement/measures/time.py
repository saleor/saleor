from measurement.base import MeasureBase


__all__ = [
    'Time',
]


class Time(MeasureBase):

    """ Time measurements (generally for multidimensional measures).

    Please do not use this for handling durations of time unrelated to
    measure classes -- python's built-in datetime module has much better
    functionality for handling intervals of time than this class provides.

    """
    STANDARD_UNIT = 's'
    UNITS = {
        's': 1.0,
        'min': 60.0,
        'hr': 3600.0,
        'day': 86400.0
    }
    ALIAS = {
        'second': 's',
        'sec': 's',  # For backward compatibility
        'minute': 'min',
        'hour': 'hr',
        'day': 'day'
    }
    SI_UNITS = ['s']
