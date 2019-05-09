# -*- coding: utf-8 -*-

# Copyright (c) 2018, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

from aniso8601 import compat

class DateResolution(object):
    Year, Month, Week, Weekday, Day, Ordinal = list(compat.range(6))

class TimeResolution(object):
    Seconds, Minutes, Hours = list(compat.range(3))
