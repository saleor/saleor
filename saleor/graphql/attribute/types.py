import re

import graphene

from ...attribute import AttributeInputType, models
from ..core.connection import CountableDjangoObjectType
from ..core.types import File
from ..decorators import (
    check_attribute_required_permissions,
    check_attribute_value_required_permissions,
)
from ..meta.types import ObjectWithMetadata
from ..translations.fields import TranslationField
from ..translations.types import AttributeTranslation, AttributeValueTranslation
from .dataloaders import AttributesByAttributeId, AttributeValuesByAttributeIdLoader
from .descriptions import AttributeDescriptions, AttributeValueDescriptions
from .enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum

COLOR_PATTERN = r"^(#[0-9a-fA-F]{3}|#(?:[0-9a-fA-F]{2}){2,4}|(rgb|hsl)a?\((-?\d+%?[,\s]+){2,3}\s*[\d\.]+%?\))$"  # noqa
color_pattern = re.compile(COLOR_PATTERN)


class AttributeValue(CountableDjangoObjectType):
    name = graphene.String(description=AttributeValueDescriptions.NAME)
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)
    translation = TranslationField(
        AttributeValueTranslation, type_name="attribute value"
    )
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    reference = graphene.ID(description="The ID of the attribute reference.")
    file = graphene.Field(
        File, description=AttributeValueDescriptions.FILE, required=False
    )

    class Meta:
        description = "Represents a value of an attribute."
        only_fields = ["id"]
        interfaces = [graphene.relay.Node]
        model = models.AttributeValue

    @staticmethod
    @check_attribute_value_required_permissions()
    def resolve_input_type(root: models.AttributeValue, *_args):
        return root.input_type

    @staticmethod
    def resolve_file(root: models.AttributeValue, *_args):
        if not root.file_url:
            return
        return File(url=root.file_url, content_type=root.content_type)

    @staticmethod
    def resolve_reference(root: models.AttributeValue, info, **_kwargs):
        def prepare_reference(attribute):
            if attribute.input_type != AttributeInputType.REFERENCE:
                return
            reference_pk = root.slug.split("_")[1]
            reference_id = graphene.Node.to_global_id(
                attribute.entity_type, reference_pk
            )
            return reference_id

        return (
            AttributesByAttributeId(info.context)
            .load(root.attribute_id)
            .then(prepare_reference)
        )


class Attribute(CountableDjangoObjectType):
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    entity_type = AttributeEntityTypeEnum(
        description=AttributeDescriptions.ENTITY_TYPE, required=False
    )

    name = graphene.String(description=AttributeDescriptions.NAME)
    slug = graphene.String(description=AttributeDescriptions.SLUG)
    type = AttributeTypeEnum(description=AttributeDescriptions.TYPE)

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
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Attribute

    @staticmethod
    def resolve_values(root: models.Attribute, info):
        return AttributeValuesByAttributeIdLoader(info.context).load(root.id)

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_value_required(root: models.Attribute, *_args):
        return root.value_required

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_visible_in_storefront(root: models.Attribute, *_args):
        return root.visible_in_storefront

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_filterable_in_storefront(root: models.Attribute, *_args):
        return root.filterable_in_storefront

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_filterable_in_dashboard(root: models.Attribute, *_args):
        return root.filterable_in_dashboard

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_storefront_search_position(root: models.Attribute, *_args):
        return root.storefront_search_position

    @staticmethod
    @check_attribute_required_permissions()
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
