import decimal

import graphene
from django.conf import settings
from django_prices.utils.formatting import get_currency_fraction
from graphql.error import GraphQLError
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


class MoneyScalar(Decimal):
    """Money scalar implementation.

    Should be used in every price input field.
    Contains validations that check if the money value is not lower than 0 and
    if the value does not contain too many decimal values.
    """

    @staticmethod
    def parse_value(value):
        value = super(MoneyScalar, MoneyScalar).parse_value(value)
        if not value:
            return value
        if value < 0:
            raise GraphQLError("Money value cannot be lower than 0.")

        currency_fraction = get_currency_fraction(settings.DEFAULT_CURRENCY)
        value = value.normalize()
        if abs(value.as_tuple().exponent) > currency_fraction:
            raise GraphQLError(
                "Ensure the provided money field value has no more than "
                f"{currency_fraction} decimal places."
            )
        return value


class WeightScalar(graphene.Scalar):
    @staticmethod
    def parse_value(value):
        weight = None
        if isinstance(value, dict):
            weight = Weight(**{value["unit"]: value["value"]})
        else:
            weight = WeightScalar.parse_decimal(value)
        if weight is None:
            raise GraphQLError(f"Unsupported value: {value}")
        return weight

    @staticmethod
    def serialize(weight):
        if isinstance(weight, Weight):
            weight = convert_weight_to_default_weight_unit(weight)
            return str(weight)
        return None

    @staticmethod
    def parse_literal(node):
        weight = None
        if isinstance(node, ast.ObjectValue):
            weight = WeightScalar.parse_literal_object(node)
        else:
            weight = WeightScalar.parse_decimal(node.value)
        if weight is None:
            raise GraphQLError(f"Unsupported value: {node.value}")
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
        value = 0
        unit = get_default_weight_unit()

        for field in node.fields:
            if field.name.value == "value":
                try:
                    value = decimal.Decimal(field.value.value)
                except decimal.DecimalException:
                    raise GraphQLError(f"Unsupported value: {field.value.value}")
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
        except ValueError as e:
            raise GraphQLError(str(e))

    @staticmethod
    def parse_value(value):
        try:
            return super(UUID, UUID).parse_value(value)
        except ValueError as e:
            raise GraphQLError(str(e))
