import decimal

import graphene
from graphene.types import Scalar
from graphene_django import DjangoObjectType
from graphql.language import ast

from ....core import weight
from ..connection import CountableConnection


# FIXME: Decimal scalar implementation has been taken from Graphene repo.
# Remove it when a new version including this implementation is released.
class Decimal(Scalar):
    """
    The `Decimal` scalar type represents a python Decimal.
    """

    @staticmethod
    def serialize(dec):
        if isinstance(dec, str):
            dec = decimal.Decimal(dec)
        assert isinstance(dec, decimal.Decimal), 'Received not compatible Decimal "{}"'.format(
            repr(dec))
        return str(dec)

    @classmethod
    def parse_literal(cls, node):
        if isinstance(node, ast.StringValue):
            return cls.parse_value(node.value)

    @staticmethod
    def parse_value(value):
        try:
            return decimal.Decimal(value)
        except decimal.DecimalException:
            return None


class CountryDisplay(graphene.ObjectType):
    code = graphene.String(description='Country code.', required=True)
    country = graphene.String(description='Country.', required=True)


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
        description="""Name of a field that caused the error. A value of
        `null` indicates that the error isn't associated with a particular
        field.""", required=False)
    message = graphene.String(description='The error message.')

    class Meta:
        description = 'Represents an error in the input of a mutation.'


class LanguageDisplay(graphene.ObjectType):
    code = graphene.String(description='Language code.', required=True)
    language = graphene.String(description='Language.', required=True)


class PermissionDisplay(graphene.ObjectType):
    code = graphene.String(
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
