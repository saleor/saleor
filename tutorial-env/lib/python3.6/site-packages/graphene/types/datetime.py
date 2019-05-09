from __future__ import absolute_import

import datetime

from aniso8601 import parse_date, parse_datetime, parse_time
from graphql.language import ast

from .scalars import Scalar


class Date(Scalar):
    """
    The `Date` scalar type represents a Date
    value as specified by
    [iso8601](https://en.wikipedia.org/wiki/ISO_8601).
    """

    @staticmethod
    def serialize(date):
        if isinstance(date, datetime.datetime):
            date = date.date()
        assert isinstance(
            date, datetime.date
        ), 'Received not compatible date "{}"'.format(repr(date))
        return date.isoformat()

    @classmethod
    def parse_literal(cls, node):
        if isinstance(node, ast.StringValue):
            return cls.parse_value(node.value)

    @staticmethod
    def parse_value(value):
        try:
            return parse_date(value)
        except ValueError:
            return None


class DateTime(Scalar):
    """
    The `DateTime` scalar type represents a DateTime
    value as specified by
    [iso8601](https://en.wikipedia.org/wiki/ISO_8601).
    """

    @staticmethod
    def serialize(dt):
        assert isinstance(
            dt, (datetime.datetime, datetime.date)
        ), 'Received not compatible datetime "{}"'.format(repr(dt))
        return dt.isoformat()

    @classmethod
    def parse_literal(cls, node):
        if isinstance(node, ast.StringValue):
            return cls.parse_value(node.value)

    @staticmethod
    def parse_value(value):
        try:
            return parse_datetime(value)
        except ValueError:
            return None


class Time(Scalar):
    """
    The `Time` scalar type represents a Time value as
    specified by
    [iso8601](https://en.wikipedia.org/wiki/ISO_8601).
    """

    @staticmethod
    def serialize(time):
        assert isinstance(
            time, datetime.time
        ), 'Received not compatible time "{}"'.format(repr(time))
        return time.isoformat()

    @classmethod
    def parse_literal(cls, node):
        if isinstance(node, ast.StringValue):
            return cls.parse_value(node.value)

    @classmethod
    def parse_value(cls, value):
        try:
            return parse_time(value)
        except ValueError:
            return None
