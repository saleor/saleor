import decimal
from datetime import MAXYEAR, MINYEAR, datetime

import graphene
import pytz
from graphene.types.generic import GenericScalar
from graphql.language import ast
from measurement.measures import Weight

from ...core.weight import (
    convert_weight_to_default_weight_unit,
    get_default_weight_unit,
)


class Decimal(graphene.Float):
    """Custom Decimal implementation.

    Returns Decimal as a float in the API,
    parses float to the Decimal on the way back.
    """

    @staticmethod
    def parse_literal(node):
        try:
            return decimal.Decimal(node.value)
        except decimal.DecimalException:
            return None

    @staticmethod
    def parse_value(value):
        try:
            # Converting the float to str before parsing it to Decimal is
            # necessary to keep the decimal places as typed
            value = str(value)
            return decimal.Decimal(value)
        except decimal.DecimalException:
            return None


class PositiveDecimal(Decimal):
    """Nonnegative Decimal scalar implementation.

    Should be used in places where value must be nonnegative (0 or greater).
    """

    @staticmethod
    def parse_value(value):
        value = super(PositiveDecimal, PositiveDecimal).parse_value(value)
        if value and value < 0:
            return None
        return value


class JSON(GenericScalar):
    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.ObjectValue):
            return {
                field.name.value: GenericScalar.parse_literal(field.value)
                for field in node.fields
            }
        elif isinstance(node, ast.ListValue):
            return [GenericScalar.parse_literal(value) for value in node.values]
        return None

    @staticmethod
    def parse_value(value):
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            return [GenericScalar.parse_value(v) for v in value]
        return None


class WeightScalar(graphene.Scalar):
    @staticmethod
    def parse_value(value):
        if isinstance(value, dict):
            weight = Weight(**{value["unit"]: value["value"]})
        else:
            weight = WeightScalar.parse_decimal(value)
        return weight

    @staticmethod
    def serialize(weight):
        if isinstance(weight, Weight):
            weight = convert_weight_to_default_weight_unit(weight)
            return str(weight)
        return None

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.ObjectValue):
            weight = WeightScalar.parse_literal_object(node)
        else:
            weight = WeightScalar.parse_decimal(node.value)
        return weight

    @staticmethod
    def parse_decimal(value):
        try:
            value = decimal.Decimal(value)
        except decimal.DecimalException:
            return None
        default_unit = get_default_weight_unit()
        return Weight(**{default_unit: value})

    @staticmethod
    def parse_literal_object(node):
        value = decimal.Decimal(0)
        unit = get_default_weight_unit()

        for field in node.fields:
            if field.name.value == "value":
                try:
                    value = decimal.Decimal(field.value.value)
                except decimal.DecimalException:
                    return None
            if field.name.value == "unit":
                unit = field.value.value
        return Weight(**{unit: value})


class UUID(graphene.UUID):
    @staticmethod
    def serialize(uuid):
        return super(UUID, UUID).serialize(uuid)

    @staticmethod
    def parse_literal(node):
        try:
            return super(UUID, UUID).parse_literal(node)
        except ValueError:
            return None

    @staticmethod
    def parse_value(value):
        try:
            return super(UUID, UUID).parse_value(value)
        except ValueError:
            return None


# The custom DateTime scalar is needed as graphene.DateTime allows to save the date-time
# value in format that is not supported by datetime module.
# The custom validation makes additional check to confirm that the value is correct
# Value like this `0001-01-01T00:00:01+07:00` will generate the BC date, which without
# additional check will be saved in the database as UTC BC time:
# `0001-12-31 17:00:01+00 BC`.
class DateTime(graphene.DateTime):
    __doc__ = graphene.DateTime.__doc__

    @staticmethod
    def parse_value(value):
        parsed_value = super(DateTime, DateTime).parse_value(value)
        if parsed_value is not None and isinstance(parsed_value, datetime):
            if parsed_value.year in [MINYEAR, MAXYEAR]:
                try:
                    parsed_value.astimezone(tz=pytz.UTC)
                except OverflowError:
                    return None
        return parsed_value


# The custom Date scalar is needed as the currently used graphene 2 version is not
# supported anymore.
# The graphene.Date scalar is raising unhandled `IndexError` for the empty string,
# the custom implementation prevent such situation and returns `None` instead.
# Probably might be dropped after switching to the supported graphene version.
class Date(graphene.Date):
    __doc__ = graphene.Date.__doc__

    @staticmethod
    def parse_value(value):
        # The parse_value method is overridden to handle the empty string.
        # The current graphene version returning unhandled `IndexError`.
        if isinstance(value, str) and not value:
            return None
        return super(Date, Date).parse_value(value)


class Minute(graphene.Int):
    """The `Minute` scalar type represents number of minutes by integer value."""


class Day(graphene.Int):
    """The `Day` scalar type represents number of days by integer value."""
