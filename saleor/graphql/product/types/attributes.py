import re

import graphene
from graphene import relay

from ....core.permissions import ProductPermissions
from ....product import models
from ...core.connection import CountableDjangoObjectType
from ...decorators import permission_required
from ...meta.deprecated.resolvers import resolve_meta, resolve_private_meta
from ...meta.types import ObjectWithMetadata
from ...translations.fields import TranslationField
from ...translations.types import AttributeTranslation, AttributeValueTranslation
from ..dataloaders import AttributeValuesByAttributeIdLoader
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..enums import AttributeInputTypeEnum, AttributeValueType

COLOR_PATTERN = r"^(#[0-9a-fA-F]{3}|#(?:[0-9a-fA-F]{2}){2,4}|(rgb|hsl)a?\((-?\d+%?[,\s]+){2,3}\s*[\d\.]+%?\))$"  # noqa
color_pattern = re.compile(COLOR_PATTERN)


def resolve_attribute_value_type(attribute_value):
    if color_pattern.match(attribute_value):
        return AttributeValueType.COLOR
    if "gradient(" in attribute_value:
        return AttributeValueType.GRADIENT
    if "://" in attribute_value:
        return AttributeValueType.URL
    return AttributeValueType.STRING


class AttributeValue(CountableDjangoObjectType):
    name = graphene.String(description=AttributeValueDescriptions.NAME)
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)
    type = AttributeValueType(description=AttributeValueDescriptions.TYPE)
    translation = TranslationField(
        AttributeValueTranslation, type_name="attribute value"
    )

    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)

    class Meta:
        description = "Represents a value of an attribute."
        only_fields = ["id"]
        interfaces = [relay.Node]
        model = models.AttributeValue

    @staticmethod
    def resolve_type(root: models.AttributeValue, *_args):
        return resolve_attribute_value_type(root.value)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_input_type(root: models.AttributeValue, *_args):
        return root.input_type


class Attribute(CountableDjangoObjectType):
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)

    name = graphene.String(description=AttributeDescriptions.NAME)
    slug = graphene.String(description=AttributeDescriptions.SLUG)

    values = graphene.List(AttributeValue, description=AttributeDescriptions.VALUES)

    value_required = graphene.Boolean(
        description=AttributeDescriptions.VALUE_REQUIRED, required=True
    )
    visible_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.VISIBLE_IN_STOREFRONT, required=True
    )
    filterable_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_STOREFRONT, required=True
    )
    filterable_in_dashboard = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_DASHBOARD, required=True
    )
    available_in_grid = graphene.Boolean(
        description=AttributeDescriptions.AVAILABLE_IN_GRID, required=True
    )

    translation = TranslationField(AttributeTranslation, type_name="attribute")

    storefront_search_position = graphene.Int(
        description=AttributeDescriptions.STOREFRONT_SEARCH_POSITION, required=True
    )

    class Meta:
        description = (
            "Custom attribute of a product. Attributes can be assigned to products and "
            "variants at the product type level."
        )
        only_fields = ["id", "product_types", "product_variant_types"]
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Attribute

    @staticmethod
    def resolve_values(root: models.Attribute, info):
        return AttributeValuesByAttributeIdLoader(info.context).load(root.id)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_private_meta(root: models.Attribute, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.Attribute, _info):
        return resolve_meta(root, _info)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_value_required(root: models.Attribute, *_args):
        return root.value_required

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_visible_in_storefront(root: models.Attribute, *_args):
        return root.visible_in_storefront

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_filterable_in_storefront(root: models.Attribute, *_args):
        return root.filterable_in_storefront

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_filterable_in_dashboard(root: models.Attribute, *_args):
        return root.filterable_in_dashboard

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_storefront_search_position(root: models.Attribute, *_args):
        return root.storefront_search_position

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_available_in_grid(root: models.Attribute, *_args):
        return root.available_in_grid


class SelectedAttribute(graphene.ObjectType):
    attribute = graphene.Field(
        Attribute,
        default_value=None,
        description=AttributeDescriptions.NAME,
        required=True,
    )
    values = graphene.List(
        AttributeValue, description="Values of an attribute.", required=True
    )

    class Meta:
        description = "Represents a custom attribute."


class AttributeInput(graphene.InputObjectType):
    slug = graphene.String(required=True, description=AttributeDescriptions.SLUG)
    value = graphene.String(
        required=False,
        description=(
            "[Deprecated] Internal representation of a value (unique per attribute). "
            "This field will be removed after 2020-07-31."
        ),
    )  # deprecated
    values = graphene.List(
        graphene.String, required=False, description=AttributeValueDescriptions.SLUG
    )
