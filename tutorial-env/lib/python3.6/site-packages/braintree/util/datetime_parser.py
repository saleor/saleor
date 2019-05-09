import re
from datetime import datetime
from datetime import timedelta


_OFFSET_REGEX = re.compile(r'(\+|\-)(\d\d):(\d\d)$')
_SYMBOLS_REGEX = re.compile(r'[-:Z]')


def parse_datetime(timestamp):
    offset_matches = _OFFSET_REGEX.findall(timestamp)

    if len(offset_matches) == 0:
        timestamp = _SYMBOLS_REGEX.sub('', timestamp)
        without_seconds = datetime.strptime(timestamp[:13], '%Y%m%dT%H%M')
        seconds = timedelta(seconds=float(timestamp[13:]))
        return without_seconds + seconds
    else:
        time_without_offset = parse_datetime(timestamp[:-6])

        try:
            offset_matches = offset_matches[0]
            offset_is_negative = offset_matches[0] == '-'
            offset_hours = int(offset_matches[1])
            offset_minutes = int(offset_matches[2])
        except IndexError:
            pass
        offset = timedelta(hours=offset_hours, minutes=offset_minutes)

        if offset_is_negative:
            return time_without_offset + offset
        else:
            return time_without_offset - offset
