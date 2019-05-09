from __future__ import unicode_literals

from django.core.exceptions import ValidationError

INVALID_CENTERPOINT_ERROR_MESSAGE = (
    "%s is in invalid ppoi. A valid "
    "ppoi must provide two coordinates, one for the x axis and one "
    "for the y, where both values are between 0 and 1. You may pass it as "
    "either a two-position tuple like this: (0.5,0.5) or as a string where "
    "the two values are separated by an 'x' like this: '0.5x0.5'."
)


def validate_ppoi_tuple(value):
    """
    Validates that a tuple (`value`)...
    ...has a len of exactly 2
    ...both values are floats/ints that are greater-than-or-equal-to 0
       AND less-than-or-equal-to 1
    """
    valid = True
    while valid is True:
        if len(value) == 2 and isinstance(value, tuple):
            for x in value:
                if x >= 0 and x <= 1:
                    pass
                else:
                    valid = False
            break
        else:
            valid = False
    return valid


def validate_ppoi(value, return_converted_tuple=False):
    """
    Converts, validates and optionally returns a string with formatting:
    '%(x_axis)dx%(y_axis)d' into a two position tuple.

    If a tuple is passed to `value` it is also validated.

    Both x_axis and y_axis must be floats or ints greater
    than 0 and less than 1.
    """

    valid_ppoi = True
    to_return = None
    if isinstance(value, tuple):
        valid_ppoi = validate_ppoi_tuple(value)
        if valid_ppoi:
            to_return = value
    else:
        tup = tuple()
        try:
            string_split = [
                float(segment.strip())
                for segment in value.split('x')
                if float(segment.strip()) >= 0 and float(segment.strip()) <= 1
            ]
        except Exception:
            valid_ppoi = False
        else:
            tup = tuple(string_split)

        valid_ppoi = validate_ppoi_tuple(tup)

        if valid_ppoi:
            to_return = tup
    if not valid_ppoi:
        raise ValidationError(
            message=INVALID_CENTERPOINT_ERROR_MESSAGE % str(value),
            code='invalid_ppoi'
        )
    else:
        if to_return and return_converted_tuple is True:
            return to_return


__all__ = ['validate_ppoi_tuple', 'validate_ppoi']
