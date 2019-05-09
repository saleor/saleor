# -*- coding: utf-8 -*-

# Copyright (c) 2018, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import datetime

from aniso8601.date import parse_date
from aniso8601.exceptions import ISOFormatError, RelativeValueError
from aniso8601.time import parse_time
from aniso8601 import compat

def parse_duration(isodurationstr, relative=False):
    #Given a string representing an ISO 8601 duration, return a
    #datetime.timedelta (or dateutil.relativedelta.relativedelta
    #if relative=True) that matches the given duration. Valid formats are:
    #
    #PnYnMnDTnHnMnS (or any reduced precision equivalent)
    #P<date>T<time>

    if isodurationstr[0] != 'P':
        raise ISOFormatError('ISO 8601 duration must start with a P.')

    #If Y, M, D, H, S, or W are in the string, assume it is a specified duration
    if _has_any_component(isodurationstr, ['Y', 'M', 'D', 'H', 'S', 'W']) is True:
        return _parse_duration_prescribed(isodurationstr, relative)

    return _parse_duration_combined(isodurationstr, relative)

def _parse_duration_prescribed(durationstr, relative):
    #durationstr can be of the form PnYnMnDTnHnMnS or PnW

    #Make sure the end character is valid
    #https://bitbucket.org/nielsenb/aniso8601/issues/9/durations-with-trailing-garbage-are-parsed
    if durationstr[-1] not in ['Y', 'M', 'D', 'H', 'S', 'W']:
        raise ISOFormatError('ISO 8601 duration must end with a valid character.')

    #Make sure only the lowest order element has decimal precision
    if durationstr.count('.') > 1:
        raise ISOFormatError('ISO 8601 allows only lowest order element to have a decimal fraction.')
    elif durationstr.count('.') == 1:
        #There should only ever be 1 letter after a decimal if there is more
        #then one, the string is invalid
        lettercount = 0

        for character in durationstr.split('.')[1]:
            if character.isalpha() is True:
                lettercount += 1

            if lettercount > 1:
                raise ISOFormatError('ISO 8601 duration must end with a single valid character.')

    #Do not allow W in combination with other designators
    #https://bitbucket.org/nielsenb/aniso8601/issues/2/week-designators-should-not-be-combinable
    if durationstr.find('W') != -1 and _has_any_component(durationstr, ['Y', 'M', 'D', 'H', 'S']) is True:
        raise ISOFormatError('ISO 8601 week designators may not be combined with other time designators.')

    #Parse the elements of the duration
    if durationstr.find('T') == -1:
        years, months, weeks, days, hours, minutes, seconds = _parse_duration_prescribed_notime(durationstr)
    else:
        years, months, weeks, days, hours, minutes, seconds = _parse_duration_prescribed_time(durationstr)

    if relative is True:
        try:
            import dateutil.relativedelta

            if int(years) != years or int(months) != months:
                #https://github.com/dateutil/dateutil/issues/40
                raise RelativeValueError('Fractional months and years are not defined for relative intervals.')

            return dateutil.relativedelta.relativedelta(years=int(years), months=int(months), weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
        except ImportError:
            raise RuntimeError('dateutil must be installed for relative duration support.')

    #Note that weeks can be handled without conversion to days
    totaldays = years * 365 + months * 30 + days

    return datetime.timedelta(weeks=weeks, days=totaldays, hours=hours, minutes=minutes, seconds=seconds)

def _parse_duration_prescribed_notime(durationstr):
    #durationstr can be of the form PnYnMnD or PnW

    #Make sure no time portion is included
    #https://bitbucket.org/nielsenb/aniso8601/issues/7/durations-with-time-components-before-t
    if _has_any_component(durationstr, ['H', 'S']):
        raise ISOFormatError('ISO 8601 time components not allowed in duration without prescribed time.')

    if _component_order_correct(durationstr, ['P', 'Y', 'M', 'D', 'W']) is False:
        raise ISOFormatError('ISO 8601 duration components must be in the correct order.')

    if durationstr.find('Y') != -1:
        years = _parse_duration_element(durationstr, 'Y')
    else:
        years = 0

    if durationstr.find('M') != -1:
        months = _parse_duration_element(durationstr, 'M')
    else:
        months = 0

    if durationstr.find('W') != -1:
        weeks = _parse_duration_element(durationstr, 'W')
    else:
        weeks = 0

    if durationstr.find('D') != -1:
        days = _parse_duration_element(durationstr, 'D')
    else:
        days = 0

    #No hours, minutes or seconds
    hours = 0
    minutes = 0
    seconds = 0

    return (years, months, weeks, days, hours, minutes, seconds)

def _parse_duration_prescribed_time(durationstr):
    #durationstr can be of the form PnYnMnDTnHnMnS

    firsthalf = durationstr[:durationstr.find('T')]
    secondhalf = durationstr[durationstr.find('T'):]

    #Make sure no time portion is included in the date half
    #https://bitbucket.org/nielsenb/aniso8601/issues/7/durations-with-time-components-before-t
    if _has_any_component(firsthalf, ['H', 'S']):
        raise ISOFormatError('ISO 8601 time components not allowed in date portion of duration.')

    if _component_order_correct(firsthalf, ['P', 'Y', 'M', 'D', 'W']) is False:
        raise ISOFormatError('ISO 8601 duration components must be in the correct order.')

    #Make sure no date component is included in the time half
    if _has_any_component(secondhalf, ['Y', 'D']):
        raise ISOFormatError('ISO 8601 time components not allowed in date portion of duration.')

    if _component_order_correct(secondhalf, ['T', 'H', 'M', 'S']) is False:
        raise ISOFormatError('ISO 8601 time components in duration must be in the correct order.')

    if firsthalf.find('Y') != -1:
        years = _parse_duration_element(firsthalf, 'Y')
    else:
        years = 0

    if firsthalf.find('M') != -1:
        months = _parse_duration_element(firsthalf, 'M')
    else:
        months = 0

    if firsthalf.find('D') != -1:
        days = _parse_duration_element(firsthalf, 'D')
    else:
        days = 0

    if secondhalf.find('H') != -1:
        hours = _parse_duration_element(secondhalf, 'H')
    else:
        hours = 0

    if secondhalf.find('M') != -1:
        minutes = _parse_duration_element(secondhalf, 'M')
    else:
        minutes = 0

    if secondhalf.find('S') != -1:
        seconds = _parse_duration_element(secondhalf, 'S')
    else:
        seconds = 0

    #Weeks can't be included
    weeks = 0

    return (years, months, weeks, days, hours, minutes, seconds)

def _parse_duration_combined(durationstr, relative):
    #Period of the form P<date>T<time>

    #Split the string in to its component parts
    datepart, timepart = durationstr[1:].split('T') #We skip the 'P'

    datevalue = parse_date(datepart)
    timevalue = parse_time(timepart)

    if relative is True:
        try:
            import dateutil.relativedelta

            return dateutil.relativedelta.relativedelta(years=datevalue.year, months=datevalue.month, days=datevalue.day, hours=timevalue.hour, minutes=timevalue.minute, seconds=timevalue.second, microseconds=timevalue.microsecond)
        except ImportError:
            raise RuntimeError('dateutil must be installed for relative duration support.')
    else:
        totaldays = datevalue.year * 365 + datevalue.month * 30 + datevalue.day

        return datetime.timedelta(days=totaldays, hours=timevalue.hour, minutes=timevalue.minute, seconds=timevalue.second, microseconds=timevalue.microsecond)

def _parse_duration_element(durationstr, elementstr):
    #Extracts the specified portion of a duration, for instance, given:
    #durationstr = 'T4H5M6.1234S'
    #elementstr = 'H'
    #
    #returns 4
    #
    #Note that the string must start with a character, so its assumed the
    #full duration string would be split at the 'T'

    durationstartindex = 0
    durationendindex = durationstr.find(elementstr)

    for characterindex in compat.range(durationendindex - 1, 0, -1):
        if durationstr[characterindex].isalpha() is True:
            durationstartindex = characterindex
            break

    durationstartindex += 1

    if ',' in durationstr:
        #Replace the comma with a 'full-stop'
        durationstr = durationstr.replace(',', '.')

    if elementstr == 'S':
        #We truncate seconds to avoid precision issues with microseconds
        #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
        if '.' in durationstr[durationstartindex:durationendindex]:
            stopindex = durationstr.index('.')

            if durationendindex - stopindex > 7:
                durationendindex = stopindex + 7

    return float(durationstr[durationstartindex:durationendindex])

def _has_any_component(durationstr, components):
    #Given a duration string, and a list of components, returns True
    #if any of the listed components are present, False otherwise.
    #
    #For instance:
    #durationstr = 'P1Y'
    #components = ['Y', 'M']
    #
    #returns True
    #
    #durationstr = 'P1Y'
    #components = ['M', 'D']
    #
    #returns False

    for component in components:
        if durationstr.find(component) != -1:
            return True

    return False

def _component_order_correct(durationstr, componentorder):
    #Given a duration string, and a list of components, returns
    #True if the components are in the same order as the
    #component order list, False otherwise. Characters that
    #are present in the component order list but not in the
    #duration string are ignored.
    #
    #https://bitbucket.org/nielsenb/aniso8601/issues/8/durations-with-components-in-wrong-order
    #
    #durationstr = 'P1Y1M1D'
    #components = ['P', 'Y', 'M', 'D']
    #
    #returns True
    #
    #durationstr = 'P1Y1M'
    #components = ['P', 'Y', 'M', 'D']
    #
    #returns True
    #
    #durationstr = 'P1D1Y1M'
    #components = ['P', 'Y', 'M', 'D']
    #
    #returns False

    componentindex = 0

    for characterindex in compat.range(len(durationstr)):
        character = durationstr[characterindex]

        if character in componentorder:
            #This is a character we need to check the order of
            if character in componentorder[componentindex:]:
                componentindex = componentorder.index(character)
            else:
                #A character is out of order
                return False

    return True
