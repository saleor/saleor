import re

import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay

from ....product import models
from ...core.connection import CountableDjangoObjectType
from ...translations.enums import LanguageCodeEnum
from ...translations.resolvers import resolve_translation
from ...translations.types import (
    AttributeTranslation, AttributeValueTranslation)
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..enums import AttributeValueType

COLOR_PATTERN = r'^(#[0-9a-fA-F]{3}|#(?:[0-9a-fA-F]{2}){2,4}|(rgb|hsl)a?\((-?\d+%?[,\s]+){2,3}\s*[\d\.]+%?\))$'  # noqa
color_pattern = re.compile(COLOR_PATTERN)


def resolve_attribute_value_type(attribute_value):
    if color_pattern.match(attribute_value):
        return AttributeValueType.COLOR
    if 'gradient(' in attribute_value:
        return AttributeValueType.GRADIENT
    if '://' in attribute_value:
        return AttributeValueType.URL
    return AttributeValueType.STRING


class AttributeValue(CountableDjangoObjectType):
    name = graphene.String(description=AttributeValueDescriptions.NAME)
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)
    type = AttributeValueType(description=AttributeValueDescriptions.TYPE)
    value = graphene.String(description=AttributeValueDescriptions.VALUE)
    translation = graphene.Field(
        AttributeValueTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description='A language code to return the translation for.',
            required=True),
        description=(
            'Returns translated Attribute Value fields '
            'for the given language code.'),
        resolver=resolve_translation)

    class Meta:
        description = 'Represents a value of an attribute.'
        only_fields = ['id', 'sort_order']
        interfaces = [relay.Node]
        model = models.AttributeValue

    def resolve_type(self, *_args):
        return resolve_attribute_value_type(self.value)


class Attribute(CountableDjangoObjectType):
    name = graphene.String(description=AttributeDescriptions.NAME)
    slug = graphene.String(description=AttributeDescriptions.SLUG)
    values = gql_optimizer.field(
        graphene.List(
            AttributeValue, description=AttributeDescriptions.VALUES),
        model_field='values')
    translation = graphene.Field(
        AttributeTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description='A language code to return the translation for.',
            required=True),
        description=(
            'Returns translated Attribute fields '
            'for the given language code.'),
        resolver=resolve_translation)

    class Meta:
        description = """
            Custom attribute of a product. Attributes can be
            assigned to products and variants at the product type level."""
        only_fields = ['id', 'product_type', 'product_variant_type']
        interfaces = [relay.Node]
        model = models.Attribute

    def resolve_values(self, *_args):
        return self.values.all()


class SelectedAttribute(graphene.ObjectType):
    attribute = graphene.Field(
        Attribute, default_value=None, description=AttributeDescriptions.NAME,
        required=True)
    value = graphene.Field(
        AttributeValue, default_value=None,
        description='Value of an attribute.', required=True)

    class Meta:
        description = 'Represents a custom attribute.'


class AttributeInput(graphene.InputObjectType):
    slug = graphene.String(
        required=True, description=AttributeDescriptions.SLUG)
    value = graphene.String(
        required=True, description=AttributeValueDescriptions.SLUG)
