# -*- coding: utf-8 -*-

# Copyright (c) 2018, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

class ISOFormatError(ValueError):
    """Raised when ISO 8601 string fails a format check."""

class RelativeValueError(ValueError):
    """Raised when an invalid value is given for calendar level accuracy."""

class YearOutOfBoundsError(ValueError):
    """Raised when year exceeds limits."""

class WeekOutOfBoundsError(ValueError):
    """Raised when week exceeds a year."""

class DayOutOfBoundsError(ValueError):
    """Raised when day is outside of 1..365, 1..366 for leap year."""

class HoursOutOfBoundsError(ValueError):
    """Raise when parsed hours are greater than 24."""

class MinutesOutOfBoundsError(ValueError):
    """Raise when parsed seconds are greater than 60."""

class SecondsOutOfBoundsError(ValueError):
    """Raise when parsed seconds are greater than 60."""

class MidnightBoundsError(ValueError):
    """Raise when parsed time has an hour of 24 but is not midnight."""

class LeapSecondError(NotImplementedError):
    """Raised when attempting to parse a leap second"""
