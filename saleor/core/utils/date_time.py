import datetime


def convert_to_utc_date_time(date) -> None | datetime.datetime:
    """Convert date into utc date time."""
    if date is None:
        return None
    return datetime.datetime.combine(
        date, datetime.datetime.min.time(), tzinfo=datetime.UTC
    )
