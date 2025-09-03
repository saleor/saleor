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
from .dataloaders import AttributesByAttributeId
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
        if instance.attribute.node.input_type == AttributeInputType.SINGLE_REFERENCE:
            entity_type = cast(str, instance.attribute.node.entity_type)
            return ASSIGNED_SINGLE_REFERENCE_MAP.get(entity_type)
        if instance.attribute.node.input_type == AttributeInputType.REFERENCE:
            entity_type = cast(str, instance.attribute.node.entity_type)
            return ASSIGNED_MULTI_REFERENCE_MAP.get(entity_type)
        attr_type = ASSIGNED_ATTRIBUTE_MAP[instance.attribute.node.input_type]
        return attr_type


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
    def resolve_value(root: AssignedAttributeData, _info: ResolveInfo) -> float | None:
        if not root.values:
            return None

        attr_value = root.values[0].node
        return attr_value.numeric


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
    def resolve_value(root: AssignedAttributeData, _info: ResolveInfo) -> JSON | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return attr_value.rich_text

    @staticmethod
    def resolve_translation(
        root: AssignedAttributeData, info: ResolveInfo, *, language_code
    ) -> Promise[JSON | None] | None:
        if not root.values:
            return None

        def _wrap_translation(
            translation: AttributeValueTranslation | None,
        ) -> JSON | None:
            if translation is None:
                return None
            return translation.rich_text

        return (
            AttributeValueTranslationByIdAndLanguageCodeLoader(info.context)
            .load((root.values[0].node.id, language_code))
            .then(_wrap_translation)
        )


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
    def resolve_value(root: AssignedAttributeData, _info: ResolveInfo) -> str | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return attr_value.plain_text

    @staticmethod
    def resolve_translation(
        root: AssignedAttributeData, info: ResolveInfo, *, language_code
    ) -> Promise[str | None] | None:
        if not root.values:
            return None

        def _wrap_translation(
            translation: AttributeValueTranslation | None,
        ) -> str | None:
            if translation is None:
                return None
            return translation.plain_text

        return (
            AttributeValueTranslationByIdAndLanguageCodeLoader(info.context)
            .load((root.values[0].node.id, language_code))
            .then(_wrap_translation)
        )


class AssignedFileAttribute(BaseObjectType):
    value = graphene.Field(File, description="The assigned file.", required=False)

    class Meta:
        interfaces = [AssignedAttribute]
        description = "Represents file attribute." + ADDED_IN_322
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @staticmethod
    def resolve_value(root: AssignedAttributeData, _info: ResolveInfo) -> File | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return File(url=attr_value.file_url, content_type=attr_value.content_type)


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
    ) -> Promise[ChannelContext[page_models.Page]] | None:
        if not root.values:
            return None

        channel_slug = root.attribute.channel_slug
        attr_value = root.values[0].node

        return (
            PageByIdLoader(info.context)
            .load(attr_value.reference_page_id)
            .then(lambda page: ChannelContext(node=page, channel_slug=channel_slug))
        )


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
    ) -> Promise[ChannelContext[product_models.Product]] | None:
        if not root.values:
            return None

        channel_slug = root.attribute.channel_slug
        attr_value = root.values[0].node

        return (
            ProductByIdLoader(info.context)
            .load(attr_value.reference_product_id)
            .then(
                lambda product: ChannelContext(node=product, channel_slug=channel_slug)
            )
        )


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
    ) -> Promise[ChannelContext[product_models.ProductVariant]] | None:
        if not root.values:
            return None

        channel_slug = root.attribute.channel_slug
        attr_value = root.values[0].node

        return (
            ProductVariantByIdLoader(info.context)
            .load(attr_value.reference_variant_id)
            .then(
                lambda product_variant: ChannelContext(
                    node=product_variant, channel_slug=channel_slug
                )
            )
        )


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
    ) -> Promise[product_models.Category] | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return CategoryByIdLoader(info.context).load(attr_value.reference_category_id)


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
    ) -> Promise[ChannelContext[product_models.Collection]] | None:
        if not root.values:
            return None

        channel_slug = root.attribute.channel_slug
        attr_value = root.values[0].node

        return (
            CollectionByIdLoader(info.context)
            .load(attr_value.reference_collection_id)
            .then(
                lambda collection: ChannelContext(
                    node=collection, channel_slug=channel_slug
                )
            )
        )


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
    ) -> Promise[list[ChannelContext[page_models.Page]]]:
        if not root.values:
            return Promise.resolve([])

        channel_slug = root.attribute.channel_slug
        attr_values = [value.node for value in root.values]
        attr_values = attr_values[:limit]

        def _wrap_with_channel_context(
            pages: list[page_models.Page],
        ) -> list[ChannelContext[page_models.Page]]:
            if not pages:
                return []
            return [
                ChannelContext(node=page, channel_slug=channel_slug) for page in pages
            ]

        return (
            PageByIdLoader(info.context)
            .load_many([value.reference_page_id for value in attr_values])
            .then(_wrap_with_channel_context)
        )


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
    ) -> Promise[list[ChannelContext[product_models.Product]]]:
        if not root.values:
            return Promise.resolve([])

        channel_slug = root.attribute.channel_slug
        attr_values = [value.node for value in root.values]
        attr_values = attr_values[:limit]

        def _wrap_with_channel_context(
            products: list[product_models.Product],
        ) -> list[ChannelContext[product_models.Product]]:
            if not products:
                return []
            return [
                ChannelContext(node=product, channel_slug=channel_slug)
                for product in products
            ]

        return (
            ProductByIdLoader(info.context)
            .load_many([value.reference_product_id for value in attr_values])
            .then(_wrap_with_channel_context)
        )


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
    ) -> Promise[list[ChannelContext[product_models.ProductVariant]]]:
        if not root.values:
            return Promise.resolve([])

        channel_slug = root.attribute.channel_slug
        attr_values = [value.node for value in root.values]
        attr_values = attr_values[:limit]

        def _wrap_with_channel_context(
            variants: list[product_models.ProductVariant],
        ) -> list[ChannelContext[product_models.ProductVariant]]:
            if not variants:
                return []
            return [
                ChannelContext(node=variant, channel_slug=channel_slug)
                for variant in variants
            ]

        return (
            ProductVariantByIdLoader(info.context)
            .load_many([value.reference_variant_id for value in attr_values])
            .then(_wrap_with_channel_context)
        )


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
    ) -> Promise[list[product_models.Category]]:
        if not root.values:
            return Promise.resolve([])
        attr_values = [value.node for value in root.values]
        attr_values = attr_values[:limit]

        return CategoryByIdLoader(info.context).load_many(
            [value.reference_category_id for value in attr_values]
        )


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
    ) -> Promise[list[ChannelContext[product_models.Collection]]]:
        if not root.values:
            return Promise.resolve([])

        channel_slug = root.attribute.channel_slug
        attr_values = [value.node for value in root.values]
        attr_values = attr_values[:limit]

        def _wrap_with_channel_context(
            collections: list[product_models.Collection],
        ) -> list[ChannelContext[product_models.Collection]]:
            if not collections:
                return []
            return [
                ChannelContext(node=collection, channel_slug=channel_slug)
                for collection in collections
            ]

        return (
            CollectionByIdLoader(info.context)
            .load_many([value.reference_collection_id for value in attr_values])
            .then(_wrap_with_channel_context)
        )


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

    def resolve_value(
        root: AssignedAttributeData, info: ResolveInfo
    ) -> models.AttributeValue | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return attr_value


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
    ) -> list[models.AttributeValue]:
        values = root.values[:limit]
        return [value.node for value in values]


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
        root: AssignedAttributeData, _info: ResolveInfo
    ) -> models.AttributeValue | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return attr_value


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
    def resolve_value(root: AssignedAttributeData, _info: ResolveInfo) -> bool | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return attr_value.boolean


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
    def resolve_value(root: AssignedAttributeData, _info: ResolveInfo) -> date | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return attr_value.date_time.date() if attr_value.date_time else None


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
        root: AssignedAttributeData, _info: ResolveInfo
    ) -> datetime | None:
        if not root.values:
            return None
        attr_value = root.values[0].node
        return attr_value.date_time


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
