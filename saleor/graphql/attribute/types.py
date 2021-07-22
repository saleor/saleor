import re

import graphene

from ...attribute import AttributeInputType, AttributeType, models
from ...core.exceptions import PermissionDenied
from ...core.permissions import PagePermissions, ProductPermissions
from ...core.tracing import traced_resolver
from ...graphql.utils import get_user_or_app_from_context
from ..core.connection import CountableDjangoObjectType
from ..core.enums import MeasurementUnitsEnum
from ..core.fields import FilterInputConnectionField
from ..core.types import File
from ..core.types.common import IntRangeInput
from ..decorators import check_attribute_required_permissions
from ..meta.types import ObjectWithMetadata
from ..translations.fields import TranslationField
from ..translations.types import AttributeTranslation, AttributeValueTranslation
from .dataloaders import AttributesByAttributeId
from .descriptions import AttributeDescriptions, AttributeValueDescriptions
from .enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum
from .filters import AttributeValueFilterInput
from .sorters import AttributeChoicesSortingInput

COLOR_PATTERN = r"^(#[0-9a-fA-F]{3}|#(?:[0-9a-fA-F]{2}){2,4}|(rgb|hsl)a?\((-?\d+%?[,\s]+){2,3}\s*[\d\.]+%?\))$"  # noqa
color_pattern = re.compile(COLOR_PATTERN)


class AttributeValue(CountableDjangoObjectType):
    name = graphene.String(description=AttributeValueDescriptions.NAME)
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)
    value = graphene.String(description=AttributeValueDescriptions.VALUE)
    translation = TranslationField(
        AttributeValueTranslation, type_name="attribute value"
    )
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    reference = graphene.ID(description="The ID of the attribute reference.")
    file = graphene.Field(
        File, description=AttributeValueDescriptions.FILE, required=False
    )
    rich_text = graphene.JSONString(
        description=AttributeValueDescriptions.RICH_TEXT, required=False
    )
    boolean = graphene.Boolean(
        description=AttributeValueDescriptions.BOOLEAN, required=False
    )

    class Meta:
        description = "Represents a value of an attribute."
        only_fields = ["id"]
        interfaces = [graphene.relay.Node]
        model = models.AttributeValue

    @staticmethod
    @traced_resolver
    def resolve_input_type(root: models.AttributeValue, info, *_args):
        def _resolve_input_type(attribute):
            requester = get_user_or_app_from_context(info.context)
            if attribute.type == AttributeType.PAGE_TYPE:
                if requester.has_perm(PagePermissions.MANAGE_PAGES):
                    return attribute.input_type
                raise PermissionDenied()
            elif requester.has_perm(ProductPermissions.MANAGE_PRODUCTS):
                return attribute.input_type
            raise PermissionDenied()

        return (
            AttributesByAttributeId(info.context)
            .load(root.attribute_id)
            .then(_resolve_input_type)
        )

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
    unit = MeasurementUnitsEnum(description=AttributeDescriptions.UNIT)
    choices = FilterInputConnectionField(
        AttributeValue,
        sort_by=AttributeChoicesSortingInput(description="Sort attribute choices."),
        filter=AttributeValueFilterInput(
            description="Filtering options for attribute choices."
        ),
        description=AttributeDescriptions.VALUES,
    )

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
    def resolve_choices(root: models.Attribute, info, **_kwargs):
        if root.input_type in AttributeInputType.TYPES_WITH_CHOICES:
            return root.values.all()
        return models.AttributeValue.objects.none()

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
    values = graphene.List(
        graphene.String, required=False, description=AttributeValueDescriptions.SLUG
    )
    values_range = graphene.Field(
        IntRangeInput,
        required=False,
        description=AttributeValueDescriptions.VALUES_RANGE,
    )
    boolean = graphene.Boolean(
        required=False, description=AttributeDescriptions.BOOLEAN
    )


class AttributeValueInput(graphene.InputObjectType):
    id = graphene.ID(description="ID of the selected attribute.")
    values = graphene.List(
        graphene.NonNull(graphene.String),
        required=False,
        description=(
            "The value or slug of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
        ),
    )
    file = graphene.String(
        required=False,
        description="URL of the file attribute. Every time, a new value is created.",
    )
    content_type = graphene.String(required=False, description="File content type.")
    references = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of entity IDs that will be used as references.",
        required=False,
    )
    rich_text = graphene.JSONString(
        required=False, description="Text content in JSON format."
    )
    boolean = graphene.Boolean(
        required=False, description=AttributeValueDescriptions.BOOLEAN
    )
