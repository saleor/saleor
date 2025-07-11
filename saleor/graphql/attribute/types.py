import graphene
from django.conf import settings

from ...attribute import AttributeEntityType, AttributeInputType, models
from ...permission.enums import (
    PagePermissions,
    PageTypePermissions,
    ProductPermissions,
    ProductTypePermissions,
)
from ..core import ResolveInfo
from ..core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.context import (
    ChannelContext,
    ChannelQsContext,
    get_database_connection_name,
)
from ..core.descriptions import (
    ADDED_IN_322,
    DEFAULT_DEPRECATION_REASON,
    DEPRECATED_IN_3X_INPUT,
)
from ..core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ..core.enums import MeasurementUnitsEnum
from ..core.fields import ConnectionField, FilterConnectionField, JSONString
from ..core.scalars import Date, DateTime
from ..core.types import (
    BaseInputObjectType,
    BaseObjectType,
    DateRangeInput,
    DateTimeRangeInput,
    File,
    IntRangeInput,
    NonNullList,
)
from ..core.types.context import ChannelContextType, ChannelContextTypeForObjectType
from ..decorators import check_attribute_required_permissions
from ..meta.types import ObjectWithMetadata
from ..page.dataloaders import PageByIdLoader
from ..product.dataloaders.products import ProductByIdLoader, ProductVariantByIdLoader
from ..translations.fields import TranslationField
from ..translations.types import AttributeTranslation, AttributeValueTranslation
from .dataloaders import (
    AttributesByAttributeId,
    AttributeValuesByAttributeIdWithLimitLoader,
)
from .descriptions import AttributeDescriptions, AttributeValueDescriptions
from .enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum
from .filters import (
    AttributeValueFilterInput,
    AttributeValueWhereInput,
    search_attribute_values,
)
from .sorters import AttributeChoicesSortingInput
from .utils.shared import ENTITY_TYPE_MAPPING


def get_reference_pk(attribute, root: models.AttributeValue) -> None | int:
    if attribute.input_type != AttributeInputType.REFERENCE:
        return None
    reference_field = ENTITY_TYPE_MAPPING[attribute.entity_type].value_field
    reference_pk = getattr(root, f"{reference_field}_id", None)
    if reference_pk is None:
        return None
    return reference_pk


class AttributeValue(ChannelContextType[models.AttributeValue]):
    id = graphene.GlobalID(required=True, description="The ID of the attribute value.")
    name = graphene.String(description=AttributeValueDescriptions.NAME)
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)
    value = graphene.String(description=AttributeValueDescriptions.VALUE)
    translation = TranslationField(
        AttributeValueTranslation,
        type_name="attribute value",
        resolver=ChannelContextType.resolve_translation,
    )
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    reference = graphene.ID(description="The ID of the referenced object.")
    referenced_object = graphene.Field(
        "saleor.graphql.attribute.unions.AttributeValueReferencedObject",
        description="The object referenced by the attribute value." + ADDED_IN_322,
    )

    file = graphene.Field(
        File, description=AttributeValueDescriptions.FILE, required=False
    )
    rich_text = JSONString(
        description=AttributeValueDescriptions.RICH_TEXT, required=False
    )
    plain_text = graphene.String(
        description=AttributeValueDescriptions.PLAIN_TEXT, required=False
    )
    boolean = graphene.Boolean(
        description=AttributeValueDescriptions.BOOLEAN, required=False
    )
    date = Date(description=AttributeValueDescriptions.DATE, required=False)
    date_time = DateTime(
        description=AttributeValueDescriptions.DATE_TIME, required=False
    )
    external_reference = graphene.String(
        description="External ID of this attribute value.",
        required=False,
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = "Represents a value of an attribute."
        interfaces = [graphene.relay.Node]
        model = models.AttributeValue

    @staticmethod
    def resolve_referenced_object(
        root: ChannelContext[models.AttributeValue], info: ResolveInfo
    ):
        attr_value = root.node

        def prepare_referenced_object(attribute):
            if not attribute:
                return None
            reference_pk = get_reference_pk(attribute, attr_value)

            if reference_pk is None:
                return None

            def wrap_with_channel_context(_object):
                return ChannelContext(node=_object, channel_slug=root.channel_slug)

            if attribute.entity_type == AttributeEntityType.PRODUCT:
                return (
                    ProductByIdLoader(info.context)
                    .load(reference_pk)
                    .then(wrap_with_channel_context)
                )
            if attribute.entity_type == AttributeEntityType.PRODUCT_VARIANT:
                return (
                    ProductVariantByIdLoader(info.context)
                    .load(reference_pk)
                    .then(wrap_with_channel_context)
                )
            if attribute.entity_type == AttributeEntityType.PAGE:
                return (
                    PageByIdLoader(info.context)
                    .load(reference_pk)
                    .then(wrap_with_channel_context)
                )
            return None

        return (
            AttributesByAttributeId(info.context)
            .load(attr_value.attribute_id)
            .then(prepare_referenced_object)
        )

    def resolve_input_type(
        root: ChannelContext[models.AttributeValue], info: ResolveInfo
    ):
        attr_value = root.node
        return (
            AttributesByAttributeId(info.context)
            .load(attr_value.attribute_id)
            .then(lambda attribute: attribute.input_type)
        )

    @staticmethod
    def resolve_file(
        root: ChannelContext[models.AttributeValue], _info: ResolveInfo
    ) -> None | File:
        attr_value = root.node
        if not attr_value.file_url:
            return None
        return File(url=attr_value.file_url, content_type=attr_value.content_type)

    @staticmethod
    def resolve_reference(
        root: ChannelContext[models.AttributeValue], info: ResolveInfo
    ):
        attr_value = root.node

        def prepare_reference(attribute) -> None | str:
            reference_pk = get_reference_pk(attribute, attr_value)
            if reference_pk is None:
                return None
            return graphene.Node.to_global_id(attribute.entity_type, reference_pk)

        return (
            AttributesByAttributeId(info.context)
            .load(attr_value.attribute_id)
            .then(prepare_reference)
        )

    @staticmethod
    def resolve_date_time(
        root: ChannelContext[models.AttributeValue], info: ResolveInfo
    ):
        attr_value = root.node

        def _resolve_date(attribute):
            if attribute.input_type == AttributeInputType.DATE_TIME:
                return attr_value.date_time
            return None

        return (
            AttributesByAttributeId(info.context)
            .load(attr_value.attribute_id)
            .then(_resolve_date)
        )

    @staticmethod
    def resolve_date(root: ChannelContext[models.AttributeValue], info: ResolveInfo):
        attr_value = root.node

        def _resolve_date(attribute):
            if attribute.input_type == AttributeInputType.DATE:
                return attr_value.date_time
            return None

        return (
            AttributesByAttributeId(info.context)
            .load(attr_value.attribute_id)
            .then(_resolve_date)
        )


class AttributeValueCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        node = AttributeValue


class Attribute(ChannelContextType[models.Attribute]):
    id = graphene.GlobalID(required=True, description="The ID of the attribute.")
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    entity_type = AttributeEntityTypeEnum(
        description=AttributeDescriptions.ENTITY_TYPE, required=False
    )

    name = graphene.String(description=AttributeDescriptions.NAME)
    slug = graphene.String(description=AttributeDescriptions.SLUG)
    type = AttributeTypeEnum(description=AttributeDescriptions.TYPE)
    unit = MeasurementUnitsEnum(description=AttributeDescriptions.UNIT)
    choices = FilterConnectionField(
        AttributeValueCountableConnection,
        sort_by=AttributeChoicesSortingInput(description="Sort attribute choices."),
        filter=AttributeValueFilterInput(
            description=(
                f"Filtering options for attribute choices. {DEPRECATED_IN_3X_INPUT} "
                "Use `where` filter instead."
            ),
        ),
        where=AttributeValueWhereInput(
            description="Where filtering options for attribute choices." + ADDED_IN_322
        ),
        search=graphene.String(description="Search attribute choices." + ADDED_IN_322),
        description=(
            "A list of predefined attribute choices available for selection. "
            "Available only for attributes with predefined choices."
        ),
    )
    values = NonNullList(
        AttributeValue,
        description=(
            "List of all existing attribute values. This includes all values"
            " that have been assigned to attributes." + ADDED_IN_322
        ),
        limit=graphene.Int(
            description=(
                "Maximum number of attribute values to return. "
                "The default value is also the maximum number of values "
                "that can be fetched."
            ),
            default_value=settings.NESTED_QUERY_LIMIT,
        ),
    )

    value_required = graphene.Boolean(
        description=(
            f"{AttributeDescriptions.VALUE_REQUIRED} Requires one of the following "
            f"permissions: {PagePermissions.MANAGE_PAGES.name}, "
            f"{PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES.name}, "
            f"{ProductPermissions.MANAGE_PRODUCTS.name}, "
            f"{ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.name}."
        ),
        required=True,
    )
    visible_in_storefront = graphene.Boolean(
        description=(
            f"{AttributeDescriptions.VISIBLE_IN_STOREFRONT} Requires one of the "
            f"following permissions: {PagePermissions.MANAGE_PAGES.name}, "
            f"{PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES.name}, "
            f"{ProductPermissions.MANAGE_PRODUCTS.name}, "
            f"{ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.name}."
        ),
        required=True,
    )
    filterable_in_storefront = graphene.Boolean(
        description=(
            f"{AttributeDescriptions.FILTERABLE_IN_STOREFRONT} Requires one of the "
            f"following permissions: {PagePermissions.MANAGE_PAGES.name}, "
            f"{PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES.name}, "
            f"{ProductPermissions.MANAGE_PRODUCTS.name}, "
            f"{ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.name}."
        ),
        required=True,
        deprecation_reason=DEFAULT_DEPRECATION_REASON,
    )
    filterable_in_dashboard = graphene.Boolean(
        description=(
            f"{AttributeDescriptions.FILTERABLE_IN_DASHBOARD} Requires one of the "
            f"following permissions: {PagePermissions.MANAGE_PAGES.name}, "
            f"{PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES.name}, "
            f"{ProductPermissions.MANAGE_PRODUCTS.name}, "
            f"{ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.name}."
        ),
        required=True,
    )
    available_in_grid = graphene.Boolean(
        description=(
            f"{AttributeDescriptions.AVAILABLE_IN_GRID} Requires one of the following "
            f"permissions: {PagePermissions.MANAGE_PAGES.name}, "
            f"{PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES.name}, "
            f"{ProductPermissions.MANAGE_PRODUCTS.name}, "
            f"{ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.name}."
        ),
        required=True,
        deprecation_reason=DEFAULT_DEPRECATION_REASON,
    )
    storefront_search_position = graphene.Int(
        description=(
            f"{AttributeDescriptions.STOREFRONT_SEARCH_POSITION} Requires one of the "
            f"following permissions: {PagePermissions.MANAGE_PAGES.name}, "
            f"{PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES.name}, "
            f"{ProductPermissions.MANAGE_PRODUCTS.name}, "
            f"{ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.name}."
        ),
        required=True,
        deprecation_reason=DEFAULT_DEPRECATION_REASON,
    )
    translation = TranslationField(
        AttributeTranslation,
        type_name="attribute",
        resolver=ChannelContextType.resolve_translation,
    )
    with_choices = graphene.Boolean(
        description=AttributeDescriptions.WITH_CHOICES, required=True
    )
    product_types = ConnectionField(
        "saleor.graphql.product.types.ProductTypeCountableConnection",
        required=True,
        description=(
            "A list of product types that use this attribute as a product attribute."
        ),
    )
    product_variant_types = ConnectionField(
        "saleor.graphql.product.types.ProductTypeCountableConnection",
        required=True,
        description=(
            "A list of product types that use this attribute "
            "as a product variant attribute."
        ),
    )
    external_reference = graphene.String(
        description="External ID of this attribute.",
        required=False,
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Custom attribute of a product. Attributes can be assigned to products and "
            "variants at the product type level."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Attribute

    @staticmethod
    def resolve_choices(
        root: ChannelContext[models.Attribute], info: ResolveInfo, **kwargs
    ):
        attr = root.node
        if attr.input_type in AttributeInputType.TYPES_WITH_CHOICES:
            qs = attr.values.using(get_database_connection_name(info.context)).all()
        else:
            qs = models.AttributeValue.objects.none()

        if search := kwargs.pop("search", None):
            qs = search_attribute_values(qs, search)

        channel_context_qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)
        channel_context_qs = filter_connection_queryset(
            channel_context_qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(
            channel_context_qs, info, kwargs, AttributeValueCountableConnection
        )

    @staticmethod
    def resolve_values(
        root: ChannelContext[models.Attribute], info: ResolveInfo, limit: int, **kwargs
    ):
        attr = root.node

        def map_channel_context(values):
            return [
                ChannelContext(node=value, channel_slug=root.channel_slug)
                for value in values
            ]

        return (
            AttributeValuesByAttributeIdWithLimitLoader(info.context, limit=limit)
            .load(attr.id)
            .then(map_channel_context)
        )

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_value_required(
        root: ChannelContext[models.Attribute], _info: ResolveInfo
    ):
        return root.node.value_required

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_visible_in_storefront(
        root: ChannelContext[models.Attribute], _info: ResolveInfo
    ):
        return root.node.visible_in_storefront

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_filterable_in_storefront(
        root: ChannelContext[models.Attribute], _info: ResolveInfo
    ):
        return root.node.filterable_in_storefront

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_filterable_in_dashboard(
        root: ChannelContext[models.Attribute], _info: ResolveInfo
    ):
        return root.node.filterable_in_dashboard

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_storefront_search_position(
        root: ChannelContext[models.Attribute], _info: ResolveInfo
    ):
        return root.node.storefront_search_position

    @staticmethod
    @check_attribute_required_permissions()
    def resolve_available_in_grid(
        root: ChannelContext[models.Attribute], _info: ResolveInfo
    ):
        return root.node.available_in_grid

    @staticmethod
    def resolve_with_choices(
        root: ChannelContext[models.Attribute], _info: ResolveInfo
    ):
        return root.node.input_type in AttributeInputType.TYPES_WITH_CHOICES

    @staticmethod
    def resolve_product_types(
        root: ChannelContext[models.Attribute], info: ResolveInfo, **kwargs
    ):
        from ..product.types import ProductTypeCountableConnection

        qs = root.node.product_types.using(
            get_database_connection_name(info.context)
        ).all()
        return create_connection_slice(qs, info, kwargs, ProductTypeCountableConnection)

    @staticmethod
    def resolve_product_variant_types(
        root: ChannelContext[models.Attribute], info: ResolveInfo, **kwargs
    ):
        from ..product.types import ProductTypeCountableConnection

        qs = root.node.product_variant_types.using(
            get_database_connection_name(info.context)
        ).all()
        return create_connection_slice(qs, info, kwargs, ProductTypeCountableConnection)


class AttributeCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        node = Attribute


class AssignedVariantAttribute(BaseObjectType):
    attribute = graphene.Field(
        Attribute, description="Attribute assigned to variant.", required=True
    )
    variant_selection = graphene.Boolean(
        required=True,
        description=(
            "Determines, whether assigned attribute is "
            "allowed for variant selection. Supported variant types for "
            "variant selection are: "
            f"{AttributeInputType.ALLOWED_IN_VARIANT_SELECTION}"
        ),
    )

    class Meta:
        description = (
            "Represents assigned attribute to variant with variant selection attached."
        )
        doc_category = DOC_CATEGORY_ATTRIBUTES


class SelectedAttribute(ChannelContextTypeForObjectType):
    attribute = graphene.Field(
        Attribute,
        default_value=None,
        description=AttributeDescriptions.NAME,
        required=True,
    )
    values = NonNullList(
        AttributeValue, description="Values of an attribute.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        description = "Represents a custom attribute."


class AttributeInput(BaseInputObjectType):
    slug = graphene.String(required=True, description=AttributeDescriptions.SLUG)
    value_names = NonNullList(
        graphene.String,
        required=False,
        description=(
            "Names corresponding to the attributeValues associated with the Attribute. "
            "When specified, it filters the results to include only records with "
            "one of the matching values."
        )
        + ADDED_IN_322,
    )
    values = NonNullList(
        graphene.String,
        required=False,
        description=(
            "Slugs identifying the attributeValues associated with the Attribute. "
            "When specified, it filters the results to include only records with "
            "one of the matching values."
        ),
    )
    values_range = graphene.Field(
        IntRangeInput,
        required=False,
        description=AttributeValueDescriptions.VALUES_RANGE,
    )
    date_time = graphene.Field(
        DateTimeRangeInput,
        required=False,
        description=AttributeValueDescriptions.DATE_TIME_RANGE,
    )
    date = graphene.Field(
        DateRangeInput,
        required=False,
        description=AttributeValueDescriptions.DATE_RANGE,
    )
    boolean = graphene.Boolean(
        required=False, description=AttributeDescriptions.BOOLEAN
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeValueSelectableTypeInput(BaseInputObjectType):
    id = graphene.ID(required=False, description="ID of an attribute value.")
    external_reference = graphene.String(
        required=False, description="External reference of an attribute value."
    )
    value = graphene.String(
        required=False,
        description=(
            "The value or slug of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
        ),
    )

    class Meta:
        description = (
            "Represents attribute value.\n"
            "1. If ID is provided, then attribute value will be resolved by ID.\n"
            "2. If externalReference is provided, then attribute value will be "
            "resolved by external reference.\n"
            "3. If value is provided, then attribute value will be resolved by value. "
            "If this attribute value doesn't exist, then it will be created.\n"
            "4. If externalReference and value is provided then "
            "new attribute value will be created."
        )
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeValueInput(BaseInputObjectType):
    id = graphene.ID(description="ID of the selected attribute.", required=False)
    external_reference = graphene.String(
        description="External ID of this attribute.", required=False
    )
    values = NonNullList(
        graphene.String,
        required=False,
        description=(
            "The value or slug of an attribute to resolve. "
            "If the passed value is non-existent, it will be created. "
            + DEPRECATED_IN_3X_INPUT
        ),
    )
    dropdown = AttributeValueSelectableTypeInput(
        required=False,
        description="Attribute value ID or external reference.",
    )
    swatch = AttributeValueSelectableTypeInput(
        required=False,
        description="Attribute value ID or external reference.",
    )
    multiselect = NonNullList(
        AttributeValueSelectableTypeInput,
        required=False,
        description="List of attribute value IDs or external references.",
    )
    numeric = graphene.String(
        required=False,
        description="Numeric value of an attribute.",
    )
    file = graphene.String(
        required=False,
        description="URL of the file attribute. Every time, a new value is created.",
    )
    content_type = graphene.String(required=False, description="File content type.")
    references = NonNullList(
        graphene.ID,
        description="List of entity IDs that will be used as references.",
        required=False,
    )
    rich_text = JSONString(required=False, description="Text content in JSON format.")
    plain_text = graphene.String(required=False, description="Plain text content.")
    boolean = graphene.Boolean(
        required=False, description=AttributeValueDescriptions.BOOLEAN
    )
    date = Date(required=False, description=AttributeValueDescriptions.DATE)
    date_time = DateTime(
        required=False, description=AttributeValueDescriptions.DATE_TIME
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
