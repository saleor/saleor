from datetime import date, datetime
from typing import cast

import graphene
from promise import Promise

from ...attribute import AttributeEntityType, AttributeInputType, models
from ...page import models as page_models
from ...permission.enums import (
    PagePermissions,
    PageTypePermissions,
    ProductPermissions,
    ProductTypePermissions,
)
from ...product import models as product_models
from ..core import ResolveInfo
from ..core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.const import DEFAULT_NESTED_LIST_LIMIT
from ..core.context import (
    ChannelContext,
    ChannelQsContext,
    get_database_connection_name,
)
from ..core.descriptions import (
    ADDED_IN_322,
    DEFAULT_DEPRECATION_REASON,
    DEPRECATED_IN_3X_INPUT,
    NESTED_QUERY_LIMIT_DESCRIPTION,
)
from ..core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ..core.enums import LanguageCodeEnum, MeasurementUnitsEnum
from ..core.fields import ConnectionField, FilterConnectionField, JSONString
from ..core.scalars import JSON, Date, DateTime, PositiveInt
from ..core.types import (
    BaseInputObjectType,
    BaseInterface,
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
from ..product.dataloaders.products import (
    CategoryByIdLoader,
    CollectionByIdLoader,
    ProductByIdLoader,
    ProductVariantByIdLoader,
)
from ..translations.dataloaders import (
    AttributeValueTranslationByIdAndLanguageCodeLoader,
)
from ..translations.fields import TranslationField
from ..translations.types import AttributeTranslation, AttributeValueTranslation
from .dataloaders.assigned_attributes import (
    AttributeValuesByPageIdAndAttributeIdAndLimitLoader,
    AttributeValuesByProductIdAndAttributeIdAndLimitLoader,
    AttributeValuesByVariantIdAndAttributeIdAndLimitLoader,
)
from .dataloaders.attributes import (
    AttributesByAttributeId,
)
from .dataloaders.reference_types import (
    AttributeReferencePageTypesByAttributeIdAndLimitLoader,
    AttributeReferenceProductTypesByAttributeIdAndLimitLoader,
)
from .descriptions import AttributeDescriptions, AttributeValueDescriptions
from .enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum
from .filters import (
    AttributeValueFilterInput,
    AttributeValueWhereInput,
    search_attribute_values,
)
from .shared_filters import AssignedAttributeValueInput
from .sorters import AttributeChoicesSortingInput
from .utils.shared import ENTITY_TYPE_MAPPING, AssignedAttributeData


def get_reference_pk(attribute, root: models.AttributeValue) -> None | int:
    if attribute.input_type not in [
        AttributeInputType.REFERENCE,
        AttributeInputType.SINGLE_REFERENCE,
    ]:
        return None
    reference_field = ENTITY_TYPE_MAPPING[attribute.entity_type].value_field
    reference_pk = getattr(root, f"{reference_field}_id", None)
    if reference_pk is None:
        return None
    return reference_pk


def _resolve_referenced_product_name(
    reference_product_id: int | None, info: ResolveInfo
) -> Promise[None | str]:
    if not reference_product_id:
        return Promise.resolve(None)
    return (
        ProductByIdLoader(info.context)
        .load(reference_product_id)
        .then(lambda product: product.name if product else None)
    )


def _resolve_referenced_product_variant_name(
    reference_variant_id: int | None, info: ResolveInfo
) -> Promise[None | str]:
    if not reference_variant_id:
        return Promise.resolve(None)

    def resolve_variant_name(variant):
        if variant is None:
            return None
        return _resolve_referenced_product_name(variant.product_id, info).then(
            lambda product_name: f"{product_name}: {variant.name}"
        )

    return (
        ProductVariantByIdLoader(info.context)
        .load(reference_variant_id)
        .then(resolve_variant_name)
    )


def _resolve_referenced_page_name(
    reference_page_id: int | None, info: ResolveInfo
) -> Promise[None | str]:
    if not reference_page_id:
        return Promise.resolve(None)
    return (
        PageByIdLoader(info.context)
        .load(reference_page_id)
        .then(lambda page: page.title if page else None)
    )


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
    def resolve_name(root: ChannelContext[models.AttributeValue], info: ResolveInfo):
        attr_value = root.node

        if attr_value.reference_product_id:
            return _resolve_referenced_product_name(
                attr_value.reference_product_id, info
            )
        if attr_value.reference_variant_id:
            return _resolve_referenced_product_variant_name(
                attr_value.reference_variant_id, info
            )
        if attr_value.reference_page_id:
            return _resolve_referenced_page_name(attr_value.reference_page_id, info)
        return attr_value.name

    @staticmethod
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
    reference_types = NonNullList(
        "saleor.graphql.attribute.unions.ReferenceType",
        description=(
            "The reference types (product or page type) that are used to narrow down "
            "the choices of reference objects." + ADDED_IN_322
        ),
        required=False,
        limit=PositiveInt(
            description=NESTED_QUERY_LIMIT_DESCRIPTION,
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
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
    def resolve_reference_types(
        root: ChannelContext[models.Attribute], info: ResolveInfo, limit: int, **kwargs
    ):
        attr = root.node
        if attr.entity_type in [
            AttributeEntityTypeEnum.PRODUCT.value,
            AttributeEntityTypeEnum.PRODUCT_VARIANT.value,
        ]:
            return AttributeReferenceProductTypesByAttributeIdAndLimitLoader(
                info.context
            ).load((attr.id, limit))
        if attr.entity_type == AttributeEntityTypeEnum.PAGE.value:
            return AttributeReferencePageTypesByAttributeIdAndLimitLoader(
                info.context
            ).load((attr.id, limit))
        return []

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


class AttributeInput(BaseInputObjectType):
    slug = graphene.String(required=False, description=AttributeDescriptions.SLUG)
    value = AssignedAttributeValueInput(
        required=False,
        description=(
            "Filter by value of the attribute. Only one value input field is allowed. "
            "If provided more than one, the error will be raised. Cannot be combined "
            "with deprecated fields of `AttributeInput`. "
        ),
    )
    values = NonNullList(
        graphene.String,
        required=False,
        description=(
            "Slugs identifying the attributeValues associated with the Attribute. "
            "When specified, it filters the results to include only records with "
            "one of the matching values. Requires `slug` to be provided. "
            f" {DEPRECATED_IN_3X_INPUT} Use `value` instead."
        ),
    )
    values_range = graphene.Field(
        IntRangeInput,
        required=False,
        description=(
            AttributeValueDescriptions.VALUES_RANGE
            + " Requires `slug` to be provided. "
            f"{DEPRECATED_IN_3X_INPUT} Use `value` instead."
        ),
    )
    date_time = graphene.Field(
        DateTimeRangeInput,
        required=False,
        description=(
            AttributeValueDescriptions.DATE_TIME_RANGE
            + " Requires `slug` to be provided. "
            f"{DEPRECATED_IN_3X_INPUT} Use `value` instead."
        ),
    )
    date = graphene.Field(
        DateRangeInput,
        required=False,
        description=(
            AttributeValueDescriptions.DATE_RANGE + " Requires `slug` to be provided. "
            f"{DEPRECATED_IN_3X_INPUT} Use `value` instead."
        ),
    )
    boolean = graphene.Boolean(
        required=False,
        description=(
            AttributeDescriptions.BOOLEAN + " Requires `slug` to be provided. "
            f"{DEPRECATED_IN_3X_INPUT} Use `value` instead."
        ),
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
    reference = graphene.ID(
        required=False,
        description=(
            "ID of the referenced entity for single reference attribute." + ADDED_IN_322
        ),
    )
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


def get_attribute_values(
    root: AssignedAttributeData, info: ResolveInfo, limit: int | None
) -> Promise[list[models.AttributeValue]]:
    if root.variant_id:
        return AttributeValuesByVariantIdAndAttributeIdAndLimitLoader(
            info.context
        ).load((root.variant_id, root.attribute.id, limit))
    if root.product_id:
        return AttributeValuesByProductIdAndAttributeIdAndLimitLoader(
            info.context
        ).load((root.product_id, root.attribute.id, limit))
    if root.page_id:
        return AttributeValuesByPageIdAndAttributeIdAndLimitLoader(info.context).load(
            (root.page_id, root.attribute.id, limit)
        )
    return Promise.resolve([])


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
        description = "Represents an assigned attribute to an object."

    @staticmethod
    def resolve_attribute(
        root: AssignedAttributeData, _info: ResolveInfo
    ) -> ChannelContext[models.Attribute]:
        return ChannelContext(node=root.attribute, channel_slug=root.channel_slug)

    @staticmethod
    def resolve_values(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[list[ChannelContext[models.AttributeValue]]]:
        def _wrap_with_channel_context(
            attribute_values: list[models.AttributeValue],
        ) -> list[ChannelContext[models.AttributeValue]]:
            if not attribute_values:
                return []
            return [
                ChannelContext(node=value, channel_slug=root.channel_slug)
                for value in attribute_values
            ]

        return get_attribute_values(root, info, limit=None).then(
            _wrap_with_channel_context
        )


class AssignedAttribute(BaseInterface):
    attribute = graphene.Field(
        Attribute,
        default_value=None,
        description="Attribute assigned to an object.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        description = "Represents an attribute assigned to an object." + ADDED_IN_322

    @staticmethod
    def resolve_type(instance: AssignedAttributeData, _info):
        if instance.attribute.input_type == AttributeInputType.SINGLE_REFERENCE:
            entity_type = cast(str, instance.attribute.entity_type)
            return ASSIGNED_SINGLE_REFERENCE_MAP.get(entity_type)
        if instance.attribute.input_type == AttributeInputType.REFERENCE:
            entity_type = cast(str, instance.attribute.entity_type)
            return ASSIGNED_MULTI_REFERENCE_MAP.get(entity_type)
        attr_type = ASSIGNED_ATTRIBUTE_MAP[instance.attribute.input_type]
        return attr_type

    def resolve_attribute(root: AssignedAttributeData, _info: ResolveInfo):
        return ChannelContext(node=root.attribute, channel_slug=root.channel_slug)


class AssignedNumericAttribute(BaseObjectType):
    value = graphene.Float(
        required=False,
        description="The assigned numeric value.",
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents a numeric value of an attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[float | None]:
        def get_numeric_value(
            attribute_values: list[models.AttributeValue],
        ) -> float | None:
            if not attribute_values:
                return None
            return attribute_values[0].numeric

        return get_attribute_values(root, info, limit=1).then(get_numeric_value)


class AssignedTextAttribute(BaseObjectType):
    value = graphene.Field(
        JSON,
        description="The assigned rich text content.",
        required=False,
    )

    translation = graphene.Field(
        JSON,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            required=True,
        ),
        description="Translation of the rich text content in the specified language.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents text attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[JSON | None]:
        def get_rich_text(attribute_values: list[models.AttributeValue]) -> JSON | None:
            if not attribute_values:
                return None
            return attribute_values[0].rich_text

        return get_attribute_values(root, info, limit=1).then(get_rich_text)

    @staticmethod
    def resolve_translation(
        root: AssignedAttributeData, info: ResolveInfo, *, language_code
    ) -> Promise[Promise[JSON | None] | None]:
        def get_translation(
            translation: AttributeValueTranslation | None,
        ) -> JSON | None:
            if translation is None:
                return None
            return translation.rich_text

        def with_attribute_value(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[JSON | None] | None:
            if not attribute_values:
                return None
            return (
                AttributeValueTranslationByIdAndLanguageCodeLoader(info.context)
                .load((attribute_values[0].id, language_code))
                .then(get_translation)
            )

        return get_attribute_values(root, info, limit=1).then(with_attribute_value)


class AssignedPlainTextAttribute(BaseObjectType):
    value = graphene.String(
        description="The assigned plain text content.",
        required=False,
    )

    translation = graphene.Field(
        graphene.String,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            required=True,
        ),
        description="Translation of the plain text content in the specified language.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents plain text attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[str | None]:
        def get_plain_text(attribute_values: list[models.AttributeValue]) -> str | None:
            if not attribute_values:
                return None
            return attribute_values[0].plain_text

        return get_attribute_values(root, info, limit=1).then(get_plain_text)

    @staticmethod
    def resolve_translation(
        root: AssignedAttributeData, info: ResolveInfo, *, language_code
    ) -> Promise[Promise[str | None] | None]:
        def get_translation(
            translation: AttributeValueTranslation | None,
        ) -> str | None:
            if translation is None:
                return None
            return translation.plain_text

        def with_attribute_value(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[str | None] | None:
            if not attribute_values:
                return None
            return (
                AttributeValueTranslationByIdAndLanguageCodeLoader(info.context)
                .load((attribute_values[0].id, language_code))
                .then(get_translation)
            )

        return get_attribute_values(root, info, limit=1).then(with_attribute_value)


class AssignedFileAttribute(BaseObjectType):
    value = graphene.Field(File, description="The assigned file.", required=False)

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents file attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[File | None]:
        def get_file(attribute_values: list[models.AttributeValue]) -> File | None:
            if not attribute_values:
                return None
            return File(
                url=attribute_values[0].file_url,
                content_type=attribute_values[0].content_type,
            )

        return get_attribute_values(root, info, limit=1).then(get_file)


class AssignedSinglePageReferenceAttribute(BaseObjectType):
    value = graphene.Field(
        "saleor.graphql.page.types.Page",
        description="The assigned page reference.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents single page reference attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[Promise[ChannelContext[page_models.Page]] | None]:
        def get_page(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[ChannelContext[page_models.Page]] | None:
            if not attribute_values:
                return None
            referenced_value = attribute_values[0]
            if not referenced_value.reference_page_id:
                return None
            channel_slug = root.channel_slug
            return (
                PageByIdLoader(info.context)
                .load(referenced_value.reference_page_id)
                .then(lambda page: ChannelContext(node=page, channel_slug=channel_slug))
            )

        return get_attribute_values(root, info, limit=1).then(get_page)


class AssignedSingleProductReferenceAttribute(BaseObjectType):
    value = graphene.Field(
        "saleor.graphql.product.types.Product",
        description="The assigned product reference.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents single product reference attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[Promise[ChannelContext[product_models.Product]] | None]:
        def get_product(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[ChannelContext[product_models.Product]] | None:
            if not attribute_values:
                return None
            referenced_value = attribute_values[0]
            if not referenced_value.reference_product_id:
                return None
            channel_slug = root.channel_slug
            return (
                ProductByIdLoader(info.context)
                .load(referenced_value.reference_product_id)
                .then(
                    lambda product: ChannelContext(
                        node=product, channel_slug=channel_slug
                    )
                )
            )

        return get_attribute_values(root, info, limit=1).then(get_product)


class AssignedSingleProductVariantReferenceAttribute(BaseObjectType):
    value = graphene.Field(
        "saleor.graphql.product.types.ProductVariant",
        description="The assigned product variant reference.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = (
            "Represents single product variant reference attribute." + ADDED_IN_322
        )
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[Promise[ChannelContext[product_models.ProductVariant]] | None]:
        def get_variant(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[ChannelContext[product_models.ProductVariant]] | None:
            if not attribute_values:
                return None
            attr_value = attribute_values[0]
            if not attr_value.reference_variant_id:
                return None

            channel_slug = root.channel_slug
            return (
                ProductVariantByIdLoader(info.context)
                .load(attr_value.reference_variant_id)
                .then(
                    lambda product_variant: ChannelContext(
                        node=product_variant, channel_slug=channel_slug
                    )
                )
            )

        return get_attribute_values(root, info, limit=1).then(get_variant)


class AssignedSingleCategoryReferenceAttribute(BaseObjectType):
    value = graphene.Field(
        "saleor.graphql.product.types.Category",
        description="The assigned category reference.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents single category reference attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[Promise[product_models.Category] | None]:
        def get_category(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[product_models.Category] | None:
            if not attribute_values:
                return None
            attr_value = attribute_values[0]
            if not attr_value.reference_category_id:
                return None
            return CategoryByIdLoader(info.context).load(
                attr_value.reference_category_id
            )

        return get_attribute_values(root, info, limit=1).then(get_category)


class AssignedSingleCollectionReferenceAttribute(BaseObjectType):
    value = graphene.Field(
        "saleor.graphql.product.types.Collection",
        description="The assigned collection reference.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents single collection reference attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[Promise[ChannelContext[product_models.Collection]] | None]:
        def get_collection(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[ChannelContext[product_models.Collection]] | None:
            if not attribute_values:
                return None
            attr_value = attribute_values[0]
            if not attr_value.reference_collection_id:
                return None
            channel_slug = root.channel_slug
            return (
                CollectionByIdLoader(info.context)
                .load(attr_value.reference_collection_id)
                .then(
                    lambda collection: ChannelContext(
                        node=collection, channel_slug=channel_slug
                    )
                )
            )

        return get_attribute_values(root, info, limit=1).then(get_collection)


class AssignedMultiPageReferenceAttribute(BaseObjectType):
    value = NonNullList(
        "saleor.graphql.page.types.Page",
        description="List of assigned page references.",
        required=True,
        limit=PositiveInt(
            description=(
                "Maximum number of referenced pages to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents multi page reference attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData,
        info: ResolveInfo,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ) -> Promise[Promise[list[ChannelContext[page_models.Page]]]]:
        def _wrap_with_channel_context(
            pages: list[page_models.Page],
        ) -> list[ChannelContext[page_models.Page]]:
            if not pages:
                return []
            return [
                ChannelContext(node=page, channel_slug=root.channel_slug)
                for page in pages
            ]

        def get_pages(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[list[ChannelContext[page_models.Page]]]:
            if not attribute_values:
                return Promise.resolve([])
            page_ids = [
                value.reference_page_id
                for value in attribute_values
                if value.reference_page_id
            ]
            return (
                PageByIdLoader(info.context)
                .load_many(page_ids)
                .then(_wrap_with_channel_context)
            )

        return get_attribute_values(root, info, limit=limit).then(get_pages)


class AssignedMultiProductReferenceAttribute(BaseObjectType):
    value = NonNullList(
        "saleor.graphql.product.types.Product",
        description="List of assigned product references.",
        required=True,
        limit=PositiveInt(
            description=(
                "Maximum number of referenced products to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents multi product reference attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData,
        info: ResolveInfo,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ) -> Promise[Promise[list[ChannelContext[product_models.Product]]]]:
        def _wrap_with_channel_context(
            products: list[product_models.Product],
        ) -> list[ChannelContext[product_models.Product]]:
            if not products:
                return []
            return [
                ChannelContext(node=product, channel_slug=root.channel_slug)
                for product in products
            ]

        def get_products(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[list[ChannelContext[product_models.Product]]]:
            if not attribute_values:
                return Promise.resolve([])
            product_ids = [
                value.reference_product_id
                for value in attribute_values
                if value.reference_product_id
            ]
            return (
                ProductByIdLoader(info.context)
                .load_many(product_ids)
                .then(_wrap_with_channel_context)
            )

        return get_attribute_values(root, info, limit=limit).then(get_products)


class AssignedMultiProductVariantReferenceAttribute(BaseObjectType):
    value = NonNullList(
        "saleor.graphql.product.types.ProductVariant",
        description="List of assigned product variant references.",
        required=True,
        limit=PositiveInt(
            description=(
                "Maximum number of referenced product variants to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = (
            "Represents multi product variant reference attribute." + ADDED_IN_322
        )
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData,
        info: ResolveInfo,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ) -> Promise[Promise[list[ChannelContext[product_models.ProductVariant]]]]:
        def _wrap_with_channel_context(
            variants: list[product_models.ProductVariant],
        ) -> list[ChannelContext[product_models.ProductVariant]]:
            if not variants:
                return []
            return [
                ChannelContext(node=variant, channel_slug=root.channel_slug)
                for variant in variants
            ]

        def get_variants(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[list[ChannelContext[product_models.ProductVariant]]]:
            if not attribute_values:
                return Promise.resolve([])

            variant_ids = [
                value.reference_variant_id
                for value in attribute_values
                if value.reference_variant_id
            ]
            return (
                ProductVariantByIdLoader(info.context)
                .load_many(variant_ids)
                .then(_wrap_with_channel_context)
            )

        return get_attribute_values(root, info, limit=limit).then(get_variants)


class AssignedMultiCategoryReferenceAttribute(BaseObjectType):
    value = NonNullList(
        "saleor.graphql.product.types.Category",
        description="List of assigned category references.",
        required=True,
        limit=PositiveInt(
            description=(
                "Maximum number of referenced categories to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents multi category reference attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData,
        info: ResolveInfo,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ) -> Promise[Promise[list[product_models.Category]]]:
        def get_categories(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[list[product_models.Category]]:
            if not attribute_values:
                return Promise.resolve([])

            category_ids = [
                value.reference_category_id
                for value in attribute_values
                if value.reference_category_id
            ]
            return CategoryByIdLoader(info.context).load_many(category_ids)

        return get_attribute_values(root, info, limit=limit).then(get_categories)


class AssignedMultiCollectionReferenceAttribute(BaseObjectType):
    value = NonNullList(
        "saleor.graphql.product.types.Collection",
        description="List of assigned collection references.",
        required=True,
        limit=PositiveInt(
            description=(
                "Maximum number of referenced collections to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}"
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents multi collection reference attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData,
        info: ResolveInfo,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ) -> Promise[Promise[list[ChannelContext[product_models.Collection]]]]:
        def _wrap_with_channel_context(
            collections: list[product_models.Collection],
        ) -> list[ChannelContext[product_models.Collection]]:
            if not collections:
                return []
            return [
                ChannelContext(node=collection, channel_slug=root.channel_slug)
                for collection in collections
            ]

        def get_collections(
            attribute_values: list[models.AttributeValue],
        ) -> Promise[list[ChannelContext[product_models.Collection]]]:
            if not attribute_values:
                return Promise.resolve([])

            collection_ids = [
                value.reference_collection_id
                for value in attribute_values
                if value.reference_collection_id
            ]
            return (
                CollectionByIdLoader(info.context)
                .load_many(collection_ids)
                .then(_wrap_with_channel_context)
            )

        return get_attribute_values(root, info, limit=limit).then(get_collections)


class AssignedChoiceAttributeValue(BaseObjectType):
    name = graphene.String(description=AttributeValueDescriptions.NAME)
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)
    translation = graphene.String(
        language_code=graphene.Argument(
            LanguageCodeEnum,
            required=True,
        ),
        description="Translation of the name.",
        required=False,
    )

    class Meta:
        description = (
            "Represents a single choice value of the attribute." + ADDED_IN_322
        )
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_translation(
        root: AttributeValue, info: ResolveInfo, *, language_code
    ) -> Promise[str | None] | None:
        return (
            AttributeValueTranslationByIdAndLanguageCodeLoader(info.context)
            .load((root.id, language_code))
            .then(lambda translation: translation.name if translation else None)
        )


class AssignedSingleChoiceAttribute(BaseObjectType):
    value = graphene.Field(
        AssignedChoiceAttributeValue,
        required=False,
        description="The assigned choice value.",
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents a single choice attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[models.AttributeValue | None]:
        def get_single_choice(
            attribute_values: list[models.AttributeValue],
        ) -> models.AttributeValue | None:
            if not attribute_values:
                return None
            return attribute_values[0]

        return get_attribute_values(root, info, limit=1).then(get_single_choice)


class AssignedMultiChoiceAttribute(BaseObjectType):
    value = NonNullList(
        AssignedChoiceAttributeValue,
        required=True,
        description="List of assigned choice values.",
        limit=PositiveInt(
            description=(
                "Maximum number of choices to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents a multi choice attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData,
        info: ResolveInfo,
        limit: int = DEFAULT_NESTED_LIST_LIMIT,
    ) -> Promise[list[models.AttributeValue]]:
        def get_multi_choice(
            attribute_values: list[models.AttributeValue],
        ) -> list[models.AttributeValue]:
            if not attribute_values:
                return []
            return attribute_values

        return get_attribute_values(root, info, limit=limit).then(get_multi_choice)


class AssignedSwatchAttributeValue(BaseObjectType):
    name = graphene.String(
        description="Name of the selected swatch value. ",
        required=False,
    )
    slug = graphene.String(
        description="Slug of the selected swatch value.",
        required=False,
    )
    hex_color = graphene.String(
        required=False,
        description="Hex color code.",
    )
    file = graphene.Field(
        File, description="File associated with the attribute.", required=False
    )

    @staticmethod
    def resolve_hex_color(
        root: models.AttributeValue, _info: ResolveInfo
    ) -> str | None:
        if not root.value:
            return None
        return root.value

    @staticmethod
    def resolve_file(root: models.AttributeValue, _info: ResolveInfo) -> File | None:
        if not root.file_url:
            return None
        return File(url=root.file_url, content_type=root.content_type)

    class Meta:
        description = "Represents a single swatch value." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AssignedSwatchAttribute(BaseObjectType):
    value = graphene.Field(
        AssignedSwatchAttributeValue,
        required=False,
        description="The assigned swatch value.",
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents a swatch attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[models.AttributeValue | None]:
        def get_swatch(
            attribute_values: list[models.AttributeValue],
        ) -> models.AttributeValue | None:
            if not attribute_values:
                return None
            return attribute_values[0]

        return get_attribute_values(root, info, limit=1).then(get_swatch)


class AssignedBooleanAttribute(BaseObjectType):
    value = graphene.Boolean(
        description="The assigned boolean value.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents a boolean attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[bool | None]:
        def get_boolean(attribute_values: list[models.AttributeValue]) -> bool | None:
            if not attribute_values:
                return None
            return attribute_values[0].boolean

        return get_attribute_values(root, info, limit=1).then(get_boolean)


class AssignedDateAttribute(BaseObjectType):
    value = graphene.Field(
        Date,
        description="The assigned date value.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents a date attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[date | None]:
        def get_date(attribute_values: list[models.AttributeValue]) -> date | None:
            if not attribute_values:
                return None
            return (
                attribute_values[0].date_time.date()
                if attribute_values[0].date_time
                else None
            )

        return get_attribute_values(root, info, limit=1).then(get_date)


class AssignedDateTimeAttribute(BaseObjectType):
    value = graphene.Field(
        DateTime,
        description="The assigned date time value.",
        required=False,
    )

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents a date time attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> Promise[datetime | None]:
        def get_datetime(
            attribute_values: list[models.AttributeValue],
        ) -> datetime | None:
            if not attribute_values:
                return None
            return attribute_values[0].date_time

        return get_attribute_values(root, info, limit=1).then(get_datetime)


ASSIGNED_SINGLE_REFERENCE_MAP = {
    AttributeEntityType.PAGE: AssignedSinglePageReferenceAttribute,
    AttributeEntityType.PRODUCT: AssignedSingleProductReferenceAttribute,
    AttributeEntityType.PRODUCT_VARIANT: AssignedSingleProductVariantReferenceAttribute,
    AttributeEntityType.CATEGORY: AssignedSingleCategoryReferenceAttribute,
    AttributeEntityType.COLLECTION: AssignedSingleCollectionReferenceAttribute,
}
ASSIGNED_MULTI_REFERENCE_MAP = {
    AttributeEntityType.PAGE: AssignedMultiPageReferenceAttribute,
    AttributeEntityType.PRODUCT: AssignedMultiProductReferenceAttribute,
    AttributeEntityType.PRODUCT_VARIANT: AssignedMultiProductVariantReferenceAttribute,
    AttributeEntityType.CATEGORY: AssignedMultiCategoryReferenceAttribute,
    AttributeEntityType.COLLECTION: AssignedMultiCollectionReferenceAttribute,
}
ASSIGNED_ATTRIBUTE_MAP = {
    AttributeInputType.NUMERIC: AssignedNumericAttribute,
    AttributeInputType.RICH_TEXT: AssignedTextAttribute,
    AttributeInputType.PLAIN_TEXT: AssignedPlainTextAttribute,
    AttributeInputType.FILE: AssignedFileAttribute,
    AttributeInputType.DROPDOWN: AssignedSingleChoiceAttribute,
    AttributeInputType.MULTISELECT: AssignedMultiChoiceAttribute,
    AttributeInputType.SWATCH: AssignedSwatchAttribute,
    AttributeInputType.BOOLEAN: AssignedBooleanAttribute,
    AttributeInputType.DATE: AssignedDateAttribute,
    AttributeInputType.DATE_TIME: AssignedDateTimeAttribute,
}
ASSIGNED_ATTRIBUTE_TYPES = (
    list(ASSIGNED_ATTRIBUTE_MAP.values())
    + list(ASSIGNED_SINGLE_REFERENCE_MAP.values())
    + list(ASSIGNED_MULTI_REFERENCE_MAP.values())
)


class ObjectWithAttributes(BaseInterface):
    assigned_attribute = graphene.Field(
        AssignedAttribute,
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the attribute",
            required=True,
        ),
        description="Get a single attribute attached to the object by attribute slug."
        + ADDED_IN_322,
    )
    assigned_attributes = NonNullList(
        AssignedAttribute,
        required=True,
        description="List of attributes assigned to the object." + ADDED_IN_322,
        limit=PositiveInt(
            description=(
                "Maximum number of attributes to return. "
                f"Default is {DEFAULT_NESTED_LIST_LIMIT}."
            ),
            default_value=DEFAULT_NESTED_LIST_LIMIT,
        ),
    )

    class Meta:
        description = "An object with attributes." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES
