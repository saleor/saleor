import decimal

import graphene
from measurement.measures import Weight

from ...core.weight import convert_weight, get_default_weight_unit


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


class WeightScalar(graphene.Scalar):
    @staticmethod
    def parse_value(value):
        # Expects value to be a string "amount unit" separated by a single
        # space.
        try:
            value = decimal.Decimal(value)
        except decimal.DecimalException:
            return None
        default_unit = get_default_weight_unit()
        return Weight(**{default_unit: value})

    @staticmethod
    def serialize(weight):
        if isinstance(weight, Weight):
            default_unit = get_default_weight_unit()
            if weight.unit != default_unit:
                weight = convert_weight(weight, default_unit)
            return str(weight)
        return None

    @staticmethod
    def parse_literal(node):
        return node
