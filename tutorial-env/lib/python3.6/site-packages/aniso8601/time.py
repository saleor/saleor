# -*- coding: utf-8 -*-

# Copyright (c) 2018, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import datetime

from aniso8601.date import parse_date
from aniso8601.exceptions import HoursOutOfBoundsError, ISOFormatError, \
        LeapSecondError, MidnightBoundsError, MinutesOutOfBoundsError, \
        SecondsOutOfBoundsError
from aniso8601.resolution import TimeResolution
from aniso8601.timezone import parse_timezone

def get_time_resolution(isotimestr):
    #Valid time formats are:
    #
    #hh:mm:ss
    #hhmmss
    #hh:mm
    #hhmm
    #hh
    #hh:mm:ssZ
    #hhmmssZ
    #hh:mmZ
    #hhmmZ
    #hhZ
    #hh:mm:ss±hh:mm
    #hhmmss±hh:mm
    #hh:mm±hh:mm
    #hhmm±hh:mm
    #hh±hh:mm
    #hh:mm:ss±hhmm
    #hhmmss±hhmm
    #hh:mm±hhmm
    #hhmm±hhmm
    #hh±hhmm
    #hh:mm:ss±hh
    #hhmmss±hh
    #hh:mm±hh
    #hhmm±hh
    #hh±hh

    timestr = _split_tz(isotimestr)[0]

    if timestr.count(':') == 2:
        #hh:mm:ss
        return TimeResolution.Seconds
    elif timestr.count(':') == 1:
        #hh:mm
        return TimeResolution.Minutes

    #Format must be hhmmss, hhmm, or hh
    if timestr.find('.') == -1:
        #No time fractions
        timestrlen = len(timestr)
    else:
        #The lowest order element is a fraction
        timestrlen = len(timestr.split('.')[0])

    if timestrlen == 6:
        #hhmmss
        return TimeResolution.Seconds
    elif timestrlen == 4:
        #hhmm
        return TimeResolution.Minutes
    elif timestrlen == 2:
        #hh
        return TimeResolution.Hours

    raise ISOFormatError('"{0}" is not a valid ISO 8601 time.'.format(isotimestr))

def parse_time(isotimestr):
    #Given a string in any ISO 8601 time format, return a datetime.time object
    #that corresponds to the given time. Fixed offset tzdata will be included
    #if UTC offset is given in the input string. Valid time formats are:
    #
    #hh:mm:ss
    #hhmmss
    #hh:mm
    #hhmm
    #hh
    #hh:mm:ssZ
    #hhmmssZ
    #hh:mmZ
    #hhmmZ
    #hhZ
    #hh:mm:ss±hh:mm
    #hhmmss±hh:mm
    #hh:mm±hh:mm
    #hhmm±hh:mm
    #hh±hh:mm
    #hh:mm:ss±hhmm
    #hhmmss±hhmm
    #hh:mm±hhmm
    #hhmm±hhmm
    #hh±hhmm
    #hh:mm:ss±hh
    #hhmmss±hh
    #hh:mm±hh
    #hhmm±hh
    #hh±hh

    (timestr, tzstr) = _split_tz(isotimestr)

    if tzstr is None:
        return _parse_time_naive(timestr)
    else:
        tzinfo = parse_timezone(tzstr)

    return _parse_time_naive(timestr).replace(tzinfo=tzinfo)

def parse_datetime(isodatetimestr, delimiter='T'):
    #Given a string in ISO 8601 date time format, return a datetime.datetime
    #object that corresponds to the given date time.
    #By default, the ISO 8601 specified T delimiter is used to split the
    #date and time (<date>T<time>). Fixed offset tzdata will be included
    #if UTC offset is given in the input string.

    isodatestr, isotimestr = isodatetimestr.split(delimiter)

    datepart = parse_date(isodatestr)

    timepart = parse_time(isotimestr)

    return datetime.datetime.combine(datepart, timepart)

def _parse_time_naive(timestr):
    #timestr is of the format hh:mm:ss, hh:mm, hhmmss, hhmm, hh
    #
    #hh is between 0 and 24, 24 is not allowed in the Python time format, since
    #it represents midnight, a time of 00:00:00 is returned
    #
    #mm is between 0 and 60, with 60 used to denote a leap second
    #
    #No tzinfo will be included
    return _RESOLUTION_MAP[get_time_resolution(timestr)](timestr)

def _parse_hour(timestr):
    #Format must be hh or hh.
    isohour = float(timestr)

    if isohour == 24:
        return datetime.time(hour=0, minute=0)
    elif isohour > 24:
        raise HoursOutOfBoundsError('Hour must be between 0..24 with 24 representing midnight.')

    #Since the time constructor doesn't handle fractional hours, we put
    #the hours in to a timedelta, and add it to the time before returning
    hoursdelta = datetime.timedelta(hours=isohour)

    return _build_time(datetime.time(hour=0), hoursdelta)

def _parse_minute_time(timestr):
    #Format must be hhmm, hhmm., hh:mm or hh:mm.
    if timestr.count(':') == 1:
        #hh:mm or hh:mm.
        timestrarray = timestr.split(':')

        isohour = int(timestrarray[0])
        isominute = float(timestrarray[1])  #Minute may now be a fraction
    else:
        #hhmm or hhmm.
        isohour = int(timestr[0:2])
        isominute = float(timestr[2:])

    if isominute >= 60:
        raise MinutesOutOfBoundsError('Minutes must be less than 60.')

    if isohour == 24:
        if isominute != 0:
            raise MidnightBoundsError('Hour 24 may only represent midnight.')

        return datetime.time(hour=0, minute=0)

    #Since the time constructor doesn't handle fractional minutes, we put
    #the minutes in to a timedelta, and add it to the time before returning
    minutesdelta = datetime.timedelta(minutes=isominute)

    return _build_time(datetime.time(hour=isohour), minutesdelta)

def _parse_second_time(timestr):
    #Format must be hhmmss, hhmmss., hh:mm:ss or hh:mm:ss.
    if timestr.count(':') == 2:
        #hh:mm:ss or hh:mm:ss.
        timestrarray = timestr.split(':')

        isohour = int(timestrarray[0])
        isominute = int(timestrarray[1])

        #Since the time constructor doesn't handle fractional seconds, we put
        #the seconds in to a timedelta, and add it to the time before returning
        #The seconds value is truncated to microsecond resolution before
        #conversion:
        #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
        secondsdelta = datetime.timedelta(seconds=float(timestrarray[2][:9]))
    else:
        #hhmmss or hhmmss.
        isohour = int(timestr[0:2])
        isominute = int(timestr[2:4])

        #Since the time constructor doesn't handle fractional seconds, we put
        #the seconds in to a timedelta, and add it to the time before returning
        #The seconds value is truncated to microsecond resolution before
        #conversion:
        #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
        secondsdelta = datetime.timedelta(seconds=float(timestr[4:13]))

    if isohour == 23 and isominute == 59 and secondsdelta.seconds == 60:
        #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
        raise LeapSecondError('Leap seconds are not supported.')
    elif secondsdelta.seconds >= 60:
        #https://bitbucket.org/nielsenb/aniso8601/issues/13/parsing-of-leap-second-gives-wildly
        raise SecondsOutOfBoundsError('Seconds must be less than 60.')

    if isominute >= 60:
        raise MinutesOutOfBoundsError('Minutes must be less than 60.')

    if isohour == 24:
        #Midnight, see 4.2.1, 4.2.3
        if isominute != 0 or secondsdelta.total_seconds() != 0:
            raise MidnightBoundsError('Hour 24 may only represent midnight.')

        return datetime.time(hour=0, minute=0)

    return _build_time(datetime.time(hour=isohour, minute=isominute),
                       secondsdelta)

def _build_time(time, delta):
    #Combine today's date (just so we have a date object), the time, the
    #delta, and return the time component
    base_datetime = datetime.datetime.combine(datetime.date.today(), time)
    return (base_datetime + delta).time()

def _split_tz(isotimestr):
    if isotimestr.find('+') != -1:
        timestr = isotimestr[0:isotimestr.find('+')]
        tzstr = isotimestr[isotimestr.find('+'):]
    elif isotimestr.find('-') != -1:
        timestr = isotimestr[0:isotimestr.find('-')]
        tzstr = isotimestr[isotimestr.find('-'):]
    elif isotimestr.endswith('Z'):
        timestr = isotimestr[:-1]
        tzstr = 'Z'
    else:
        timestr = isotimestr
        tzstr = None
    return (timestr, tzstr)

_RESOLUTION_MAP = {
    TimeResolution.Hours: _parse_hour,
    TimeResolution.Minutes: _parse_minute_time,
    TimeResolution.Seconds: _parse_second_time
}
