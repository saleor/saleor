from datetime import datetime

import pytz


def convert_to_utc_date_time(date):
    """Convert date into utc date time."""
    return datetime.combine(date, datetime.min.time(), tzinfo=pytz.UTC)
