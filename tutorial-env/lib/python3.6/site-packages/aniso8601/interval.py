# -*- coding: utf-8 -*-

# Copyright (c) 2018, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

from datetime import datetime
from aniso8601.duration import parse_duration
from aniso8601.exceptions import ISOFormatError
from aniso8601.time import parse_datetime
from aniso8601.date import parse_date

def parse_interval(isointervalstr, intervaldelimiter='/', datetimedelimiter='T', relative=False):
    #Given a string representing an ISO 8601 interval, return a
    #tuple of datetime.date or date.datetime objects representing the beginning
    #and end of the specified interval. Valid formats are:
    #
    #<start>/<end>
    #<start>/<duration>
    #<duration>/<end>
    #
    #The <start> and <end> values can represent dates, or datetimes,
    #not times.
    #
    #The format:
    #
    #<duration>
    #
    #Is expressly not supported as there is no way to provide the addtional
    #required context.

    if isointervalstr[0] == 'R':
        raise ISOFormatError('ISO 8601 repeating intervals must be parsed with parse_repeating_interval.')

    interval_parts = _parse_interval_parts(isointervalstr, intervaldelimiter, datetimedelimiter, relative)

    return (interval_parts[0], interval_parts[1])

def parse_repeating_interval(isointervalstr, intervaldelimiter='/', datetimedelimiter='T', relative=False):
    #Given a string representing an ISO 8601 interval repating, return a
    #generator of datetime.date or date.datetime objects representing the
    #dates specified by the repeating interval. Valid formats are:
    #
    #Rnn/<interval>
    #R/<interval>

    if isointervalstr[0] != 'R':
        raise ISOFormatError('ISO 8601 repeating interval must start with an R.')

    #Parse the number of iterations
    iterationpart, intervalpart = isointervalstr.split(intervaldelimiter, 1)

    if len(iterationpart) > 1:
        iterations = int(iterationpart[1:])
    else:
        iterations = None

    interval_parts = _parse_interval_parts(intervalpart, intervaldelimiter, datetimedelimiter, relative=relative)

    #Now, build and return the generator
    if iterations is not None:
        return _date_generator(interval_parts[0], interval_parts[2], iterations)

    return _date_generator_unbounded(interval_parts[0], interval_parts[2])

def _parse_interval_parts(isointervalstr, intervaldelimiter='/', datetimedelimiter='T', relative=False):
    #Returns a tuple containing the start of the interval, the end of the interval, and the interval timedelta

    firstpart, secondpart = isointervalstr.split(intervaldelimiter)

    if firstpart[0] == 'P':
        #<duration>/<end>
        #Notice that these are not returned 'in order' (earlier to later), this
        #is to maintain consistency with parsing <start>/<end> durations, as
        #well as making repeating interval code cleaner. Users who desire
        #durations to be in order can use the 'sorted' operator.

        #We need to figure out if <end> is a date, or a datetime
        if secondpart.find(datetimedelimiter) != -1:
            #<end> is a datetime
            duration = parse_duration(firstpart, relative=relative)
            enddatetime = parse_datetime(secondpart, delimiter=datetimedelimiter)

            return (enddatetime, enddatetime - duration, -duration)

        #<end> must just be a date
        duration = parse_duration(firstpart, relative=relative)
        enddate = parse_date(secondpart)

        #See if we need to upconvert to datetime to preserve resolution
        if firstpart.find(datetimedelimiter) != -1:
            return (enddate, datetime.combine(enddate, datetime.min.time()) - duration, -duration)

        return (enddate, enddate - duration, -duration)
    elif secondpart[0] == 'P':
        #<start>/<duration>
        #We need to figure out if <start> is a date, or a datetime
        if firstpart.find(datetimedelimiter) != -1:
            #<start> is a datetime
            duration = parse_duration(secondpart, relative=relative)
            startdatetime = parse_datetime(firstpart, delimiter=datetimedelimiter)

            return (startdatetime, startdatetime + duration, duration)

        #<start> must just be a date
        duration = parse_duration(secondpart, relative=relative)
        startdate = parse_date(firstpart)

        #See if we need to upconvert to datetime to preserve resolution
        if secondpart.find(datetimedelimiter) != -1:
            return (startdate, datetime.combine(startdate, datetime.min.time()) + duration, duration)

        return (startdate, startdate + duration, duration)

    #<start>/<end>
    if firstpart.find(datetimedelimiter) != -1 and secondpart.find(datetimedelimiter) != -1:
        #Both parts are datetimes
        start_datetime = parse_datetime(firstpart, delimiter=datetimedelimiter)
        end_datetime = parse_datetime(secondpart, delimiter=datetimedelimiter)

        return (start_datetime, end_datetime, end_datetime - start_datetime)
    elif firstpart.find(datetimedelimiter) != -1 and secondpart.find(datetimedelimiter) == -1:
        #First part is a datetime, second part is a date
        start_datetime = parse_datetime(firstpart, delimiter=datetimedelimiter)
        end_date = parse_date(secondpart)

        return (start_datetime, end_date, datetime.combine(end_date, datetime.min.time()) - start_datetime)
    elif firstpart.find(datetimedelimiter) == -1 and secondpart.find(datetimedelimiter) != -1:
        #First part is a date, second part is a datetime
        start_date = parse_date(firstpart)
        end_datetime = parse_datetime(secondpart, delimiter=datetimedelimiter)

        return (start_date, end_datetime, end_datetime - datetime.combine(start_date, datetime.min.time()))

    #Both parts are dates
    start_date = parse_date(firstpart)
    end_date = parse_date(secondpart)

    return (start_date, end_date, end_date - start_date)

def _date_generator(startdate, timedelta, iterations):
    currentdate = startdate
    currentiteration = 0

    while currentiteration < iterations:
        yield currentdate

        #Update the values
        currentdate += timedelta
        currentiteration += 1

def _date_generator_unbounded(startdate, timedelta):
    currentdate = startdate

    while True:
        yield currentdate

        #Update the value
        currentdate += timedelta
