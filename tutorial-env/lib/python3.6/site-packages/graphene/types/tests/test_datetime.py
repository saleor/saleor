import datetime

import pytz
from graphql import GraphQLError

from ..datetime import Date, DateTime, Time
from ..objecttype import ObjectType
from ..schema import Schema


class Query(ObjectType):
    datetime = DateTime(_in=DateTime(name="in"))
    date = Date(_in=Date(name="in"))
    time = Time(_at=Time(name="at"))

    def resolve_datetime(self, info, _in=None):
        return _in

    def resolve_date(self, info, _in=None):
        return _in

    def resolve_time(self, info, _at=None):
        return _at


schema = Schema(query=Query)


def test_datetime_query():
    now = datetime.datetime.now().replace(tzinfo=pytz.utc)
    isoformat = now.isoformat()

    result = schema.execute("""{ datetime(in: "%s") }""" % isoformat)
    assert not result.errors
    assert result.data == {"datetime": isoformat}


def test_date_query():
    now = datetime.datetime.now().replace(tzinfo=pytz.utc).date()
    isoformat = now.isoformat()

    result = schema.execute("""{ date(in: "%s") }""" % isoformat)
    assert not result.errors
    assert result.data == {"date": isoformat}


def test_time_query():
    now = datetime.datetime.now().replace(tzinfo=pytz.utc)
    time = datetime.time(now.hour, now.minute, now.second, now.microsecond, now.tzinfo)
    isoformat = time.isoformat()

    result = schema.execute("""{ time(at: "%s") }""" % isoformat)
    assert not result.errors
    assert result.data == {"time": isoformat}


def test_bad_datetime_query():
    not_a_date = "Some string that's not a date"

    result = schema.execute("""{ datetime(in: "%s") }""" % not_a_date)

    assert len(result.errors) == 1
    assert isinstance(result.errors[0], GraphQLError)
    assert result.data is None


def test_bad_date_query():
    not_a_date = "Some string that's not a date"

    result = schema.execute("""{ date(in: "%s") }""" % not_a_date)

    assert len(result.errors) == 1
    assert isinstance(result.errors[0], GraphQLError)
    assert result.data is None


def test_bad_time_query():
    not_a_date = "Some string that's not a date"

    result = schema.execute("""{ time(at: "%s") }""" % not_a_date)

    assert len(result.errors) == 1
    assert isinstance(result.errors[0], GraphQLError)
    assert result.data is None


def test_datetime_query_variable():
    now = datetime.datetime.now().replace(tzinfo=pytz.utc)
    isoformat = now.isoformat()

    result = schema.execute(
        """query Test($date: DateTime){ datetime(in: $date) }""",
        variable_values={"date": isoformat},
    )
    assert not result.errors
    assert result.data == {"datetime": isoformat}


def test_date_query_variable():
    now = datetime.datetime.now().replace(tzinfo=pytz.utc).date()
    isoformat = now.isoformat()

    result = schema.execute(
        """query Test($date: Date){ date(in: $date) }""",
        variable_values={"date": isoformat},
    )
    assert not result.errors
    assert result.data == {"date": isoformat}


def test_time_query_variable():
    now = datetime.datetime.now().replace(tzinfo=pytz.utc)
    time = datetime.time(now.hour, now.minute, now.second, now.microsecond, now.tzinfo)
    isoformat = time.isoformat()

    result = schema.execute(
        """query Test($time: Time){ time(at: $time) }""",
        variable_values={"time": isoformat},
    )
    assert not result.errors
    assert result.data == {"time": isoformat}
