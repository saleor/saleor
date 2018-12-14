import decimal
from textwrap import dedent

import graphene
from graphene_django import DjangoObjectType

from saleor.core.permissions import MODELS_PERMISSIONS
from saleor.graphql.core.utils import str_to_enum

from ....core import weight
from ..connection import CountableConnection
from .money import VAT


class ReportingPeriod(graphene.Enum):
    TODAY = 'TODAY'
    THIS_MONTH = 'THIS_MONTH'


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


class CountryDisplay(graphene.ObjectType):
    code = graphene.String(description='Country code.', required=True)
    country = graphene.String(description='Country name.', required=True)
    vat = graphene.Field(VAT, description='Country tax.')


class CountableDjangoObjectType(DjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        # Force it to use the countable connection
        countable_conn = CountableConnection.create_type(
            "{}CountableConnection".format(cls.__name__),
            node=cls)
        super().__init_subclass_with_meta__(
            *args, connection=countable_conn, **kwargs)


class Error(graphene.ObjectType):
    field = graphene.String(
        description=dedent("""Name of a field that caused the error. A value of
        `null` indicates that the error isn't associated with a particular
        field."""), required=False)
    message = graphene.String(description='The error message.')

    class Meta:
        description = 'Represents an error in the input of a mutation.'


class LanguageDisplay(graphene.ObjectType):
    code = graphene.String(description='Language code.', required=True)
    language = graphene.String(description='Language.', required=True)


PermissionEnum = graphene.Enum(
    'PermissionEnum', [
        (str_to_enum(codename.split('.')[1]), codename)
        for codename in MODELS_PERMISSIONS])


class PermissionDisplay(graphene.ObjectType):
    code = PermissionEnum(
        description='Internal code for permission.', required=True)
    name = graphene.String(
        description='Describe action(s) allowed to do by permission.',
        required=True)

    class Meta:
        description = 'Represents a permission object in a friendly form.'


class SeoInput(graphene.InputObjectType):
    title = graphene.String(description='SEO title.')
    description = graphene.String(description='SEO description.')


class Weight(graphene.ObjectType):
    unit = graphene.String(description='Weight unit', required=True)
    value = graphene.Float(description='Weight value', required=True)

    class Meta:
        description = 'Represents weight value in a specific weight unit.'


WeightUnitsEnum = graphene.Enum.from_enum(weight.WeightUnitsEnum)
