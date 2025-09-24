from typing import Literal

import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet
from django.utils import timezone

from ....attribute.models import (
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    Attribute,
    AttributeValue,
)
from ....product.models import Product, ProductVariant
from ...attribute.shared_filters import (
    CONTAINS_TYPING,
    AssignedAttributeWhereInput,
    clean_up_referenced_global_ids,
    get_attribute_values_by_boolean_value,
    get_attribute_values_by_date_time_value,
    get_attribute_values_by_date_value,
    get_attribute_values_by_numeric_value,
    get_attribute_values_by_referenced_category_ids,
    get_attribute_values_by_referenced_category_slugs,
    get_attribute_values_by_referenced_collection_ids,
    get_attribute_values_by_referenced_collection_slugs,
    get_attribute_values_by_referenced_page_ids,
    get_attribute_values_by_referenced_page_slugs,
    get_attribute_values_by_referenced_product_ids,
    get_attribute_values_by_referenced_product_slugs,
    get_attribute_values_by_referenced_variant_ids,
    get_attribute_values_by_referenced_variant_skus,
    get_attribute_values_by_slug_or_name_value,
    validate_attribute_value_input,
)
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeFilter,
    ListObjectTypeWhereFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
    ObjectTypeFilter,
    ObjectTypeWhereFilter,
)
from ...core.filters.where_input import StringFilterInput, WhereInputObjectType
from ...core.types import DateTimeRangeInput
from ...utils.filters import (
    Number,
    filter_by_ids,
    filter_where_by_range_field,
    filter_where_by_value_field,
)
from .shared import filter_updated_at_range


def filter_sku_list(qs, _, value):
    return qs.filter(sku__in=value)


def filter_is_preorder(qs, _, value):
    if value:
        return qs.filter(is_preorder=True).filter(
            Q(preorder_end_date__isnull=True) | Q(preorder_end_date__gte=timezone.now())
        )
    return qs.filter(
        Q(is_preorder=False)
        | (Q(is_preorder=True)) & Q(preorder_end_date__lt=timezone.now())
    )


def filter_by_slug_or_name(
    attr_id: int | None,
    attr_value: dict,
    db_connection_name: str,
):
    attribute_values = get_attribute_values_by_slug_or_name_value(
        attr_id=attr_id,
        attr_value=attr_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_variant_attribute_for_attribute_value_qs(
        attribute_values,
        db_connection_name,
    )


def filter_by_numeric_attribute(
    attr_id: int | None,
    numeric_value: dict[str, Number | list[Number] | dict[str, Number]],
    db_connection_name: str,
):
    qs_by_numeric = get_attribute_values_by_numeric_value(
        attr_id=attr_id,
        numeric_value=numeric_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_variant_attribute_for_attribute_value_qs(
        qs_by_numeric,
        db_connection_name,
    )


def filter_by_boolean_attribute(
    attr_id: int | None,
    boolean_value,
    db_connection_name: str,
):
    qs_by_boolean = get_attribute_values_by_boolean_value(
        attr_id=attr_id,
        boolean_value=boolean_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_variant_attribute_for_attribute_value_qs(
        qs_by_boolean,
        db_connection_name,
    )


def filter_by_date_attribute(
    attr_id: int | None,
    date_value,
    db_connection_name: str,
):
    qs_by_date = get_attribute_values_by_date_value(
        attr_id=attr_id,
        date_value=date_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_variant_attribute_for_attribute_value_qs(
        qs_by_date,
        db_connection_name,
    )


def filter_by_date_time_attribute(
    attr_id: int | None,
    date_value,
    db_connection_name: str,
):
    qs_by_date_time = get_attribute_values_by_date_time_value(
        attr_id=attr_id,
        date_value=date_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_variant_attribute_for_attribute_value_qs(
        qs_by_date_time,
        db_connection_name,
    )


def _get_assigned_variant_attribute_for_attribute_value_qs(
    attribute_values: QuerySet[AttributeValue],
    db_connection_name: str,
):
    assigned_attr_value = AssignedVariantAttributeValue.objects.using(
        db_connection_name
    ).filter(
        value__in=attribute_values,
        assignment_id=OuterRef("id"),
    )
    return Q(
        Exists(
            AssignedVariantAttribute.objects.using(db_connection_name).filter(
                Exists(assigned_attr_value), variant_id=OuterRef("pk")
            )
        )
    )


def _filter_contains_single_expression(
    attr_id: int | None,
    db_connection_name: str,
    referenced_attr_values: QuerySet[AttributeValue],
):
    if attr_id:
        referenced_attr_values = referenced_attr_values.filter(
            attribute_id=attr_id,
        )
    assigned_attr_value = AssignedVariantAttributeValue.objects.using(
        db_connection_name
    ).filter(
        value__in=referenced_attr_values,
        assignment_id=OuterRef("id"),
    )
    return Q(
        Exists(
            AssignedVariantAttribute.objects.using(db_connection_name).filter(
                Exists(assigned_attr_value), variant_id=OuterRef("pk")
            )
        )
    )


def filter_by_contains_referenced_page_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter variants based on their references to pages.

    - If `contains_all` is provided, only variants that reference all of the
    specified pages will match.
    - If `contains_any` is provided, variants that reference at least one of
    the specified pages will match.
    """
    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    if contains_all:
        expression = Q()
        for page_slug in contains_all:
            referenced_attr_values = get_attribute_values_by_referenced_page_slugs(
                slugs=[page_slug], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
        return expression

    if contains_any:
        referenced_attr_values = get_attribute_values_by_referenced_page_slugs(
            slugs=contains_any, db_connection_name=db_connection_name
        )
        return _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    return Q()


def filter_by_contains_referenced_category_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter variants based on their references to categories.

    - If `contains_all` is provided, only variants that reference all of the
    specified categories will match.
    - If `contains_any` is provided, variants that reference at least one of
    the specified categories will match.
    """
    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    if contains_all:
        expression = Q()
        for category_slug in contains_all:
            referenced_attr_values = get_attribute_values_by_referenced_category_slugs(
                slugs=[category_slug], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
        return expression

    if contains_any:
        referenced_attr_values = get_attribute_values_by_referenced_category_slugs(
            slugs=contains_any, db_connection_name=db_connection_name
        )
        return _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    return Q()


def filter_by_contains_referenced_collection_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter variants based on their references to collections.

    - If `contains_all` is provided, only variants that reference all of the
    specified collections will match.
    - If `contains_any` is provided, variants that reference at least one of
    the specified collections will match.
    """
    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    if contains_all:
        expression = Q()
        for collection_slug in contains_all:
            referenced_attr_values = (
                get_attribute_values_by_referenced_collection_slugs(
                    slugs=[collection_slug], db_connection_name=db_connection_name
                )
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
        return expression

    if contains_any:
        referenced_attr_values = get_attribute_values_by_referenced_collection_slugs(
            slugs=contains_any, db_connection_name=db_connection_name
        )
        return _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    return Q()


def filter_by_contains_referenced_product_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter variants based on their references to products.

    - If `contains_all` is provided, only variants that reference all of the
    specified products will match.
    - If `contains_any` is provided, variants that reference at least one of
    the specified products will match.
    """
    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    if contains_all:
        expression = Q()
        for product_slug in contains_all:
            referenced_attr_values = get_attribute_values_by_referenced_product_slugs(
                slugs=[product_slug], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
        return expression

    if contains_any:
        referenced_attr_values = get_attribute_values_by_referenced_product_slugs(
            slugs=contains_any, db_connection_name=db_connection_name
        )
        return _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    return Q()


def filter_by_contains_referenced_variant_skus(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter variants based on their references to variants.

    - If `contains_all` is provided, only variants that reference all of the
    specified variants will match.
    - If `contains_any` is provided, variants that reference at least one of
    the specified variants will match.
    """
    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    if contains_all:
        expression = Q()
        for variant_sku in contains_all:
            referenced_attr_values = get_attribute_values_by_referenced_variant_skus(
                slugs=[variant_sku], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
        return expression

    if contains_any:
        referenced_attr_values = get_attribute_values_by_referenced_variant_skus(
            slugs=contains_any, db_connection_name=db_connection_name
        )
        return _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    return Q()


def _filter_by_contains_all_referenced_object_ids(
    variant_ids: set[int],
    product_ids: set[int],
    page_ids: set[int],
    category_ids: set[int],
    collection_ids: set[int],
    attr_id: int | None,
    db_connection_name: str,
) -> Q:
    expression = Q()
    if page_ids:
        for page_id in page_ids:
            referenced_attr_values = get_attribute_values_by_referenced_page_ids(
                ids=[page_id], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
    if product_ids:
        for product_id in product_ids:
            referenced_attr_values = get_attribute_values_by_referenced_product_ids(
                ids=[product_id], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
    if variant_ids:
        for variant_id in variant_ids:
            referenced_attr_values = get_attribute_values_by_referenced_variant_ids(
                ids=[variant_id], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
    if category_ids:
        for category_id in category_ids:
            referenced_attr_values = get_attribute_values_by_referenced_category_ids(
                ids=[category_id], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
    if collection_ids:
        for collection_id in collection_ids:
            referenced_attr_values = get_attribute_values_by_referenced_collection_ids(
                ids=[collection_id], db_connection_name=db_connection_name
            )
            expression &= _filter_contains_single_expression(
                attr_id=attr_id,
                db_connection_name=db_connection_name,
                referenced_attr_values=referenced_attr_values,
            )
    return expression


def _filter_by_contains_any_referenced_object_ids(
    variant_ids: set[int],
    product_ids: set[int],
    page_ids: set[int],
    category_ids: set[int],
    collection_ids: set[int],
    attr_id: int | None,
    db_connection_name: str,
) -> Q:
    expression = Q()
    if page_ids:
        referenced_attr_values = get_attribute_values_by_referenced_page_ids(
            ids=list(page_ids), db_connection_name=db_connection_name
        )
        expression |= _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    if product_ids:
        referenced_attr_values = get_attribute_values_by_referenced_product_ids(
            ids=list(product_ids), db_connection_name=db_connection_name
        )
        expression |= _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    if variant_ids:
        referenced_attr_values = get_attribute_values_by_referenced_variant_ids(
            ids=list(variant_ids), db_connection_name=db_connection_name
        )
        expression |= _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    if category_ids:
        referenced_attr_values = get_attribute_values_by_referenced_category_ids(
            ids=list(category_ids), db_connection_name=db_connection_name
        )
        expression |= _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    if collection_ids:
        referenced_attr_values = get_attribute_values_by_referenced_collection_ids(
            ids=list(collection_ids), db_connection_name=db_connection_name
        )
        expression |= _filter_contains_single_expression(
            attr_id=attr_id,
            db_connection_name=db_connection_name,
            referenced_attr_values=referenced_attr_values,
        )
    return expression


def filter_by_contains_referenced_object_ids(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
) -> Q:
    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    grouped_ids = clean_up_referenced_global_ids(contains_any or contains_all or [])
    variant_ids = grouped_ids["ProductVariant"]
    product_ids = grouped_ids["Product"]
    page_ids = grouped_ids["Page"]
    category_ids = grouped_ids["Category"]
    collection_ids = grouped_ids["Collection"]

    if contains_all:
        return _filter_by_contains_all_referenced_object_ids(
            variant_ids=variant_ids,
            product_ids=product_ids,
            page_ids=page_ids,
            category_ids=category_ids,
            collection_ids=collection_ids,
            attr_id=attr_id,
            db_connection_name=db_connection_name,
        )
    if contains_any:
        return _filter_by_contains_any_referenced_object_ids(
            variant_ids=variant_ids,
            product_ids=product_ids,
            page_ids=page_ids,
            category_ids=category_ids,
            collection_ids=collection_ids,
            attr_id=attr_id,
            db_connection_name=db_connection_name,
        )
    return Q()


def filter_objects_by_reference_attributes(
    attr_id: int | None,
    attr_value: dict[
        Literal[
            "referenced_ids",
            "page_slugs",
            "product_slugs",
            "product_variant_skus",
            "category_slugs",
            "collection_slugs",
        ],
        CONTAINS_TYPING,
    ],
    db_connection_name: str,
):
    filter_expression = Q()

    if "referenced_ids" in attr_value:
        filter_expression &= filter_by_contains_referenced_object_ids(
            attr_id,
            attr_value["referenced_ids"],
            db_connection_name,
        )
    if "page_slugs" in attr_value:
        filter_expression &= filter_by_contains_referenced_page_slugs(
            attr_id,
            attr_value["page_slugs"],
            db_connection_name,
        )
    if "product_slugs" in attr_value:
        filter_expression &= filter_by_contains_referenced_product_slugs(
            attr_id,
            attr_value["product_slugs"],
            db_connection_name,
        )
    if "product_variant_skus" in attr_value:
        filter_expression &= filter_by_contains_referenced_variant_skus(
            attr_id,
            attr_value["product_variant_skus"],
            db_connection_name,
        )
    if "category_slugs" in attr_value:
        filter_expression &= filter_by_contains_referenced_category_slugs(
            attr_id,
            attr_value["category_slugs"],
            db_connection_name,
        )
    if "collection_slugs" in attr_value:
        filter_expression &= filter_by_contains_referenced_collection_slugs(
            attr_id,
            attr_value["collection_slugs"],
            db_connection_name,
        )
    return filter_expression


def filter_variants_by_attributes(
    qs: QuerySet[ProductVariant], value: list[dict]
) -> QuerySet[ProductVariant]:
    attribute_slugs = {
        attr_filter["slug"] for attr_filter in value if "slug" in attr_filter
    }
    attributes_map = {
        attr.slug: attr
        for attr in Attribute.objects.using(qs.db).filter(slug__in=attribute_slugs)
    }
    if len(attribute_slugs) != len(attributes_map.keys()):
        # Filter over non existing attribute
        return qs.none()

    attr_filter_expression = Q()

    attr_without_values_input = []
    for attr_filter in value:
        if "slug" in attr_filter and "value" not in attr_filter:
            attr_without_values_input.append(attributes_map[attr_filter["slug"]])

    if attr_without_values_input:
        atr_value_qs = AttributeValue.objects.using(qs.db).filter(
            attribute_id__in=[attr.id for attr in attr_without_values_input]
        )
        attr_filter_expression = _get_assigned_variant_attribute_for_attribute_value_qs(
            atr_value_qs,
            qs.db,
        )

    for attr_filter in value:
        attr_value = attr_filter.get("value")
        if not attr_value:
            # attrs without value input are handled separately
            continue

        attr_id = None
        if attr_slug := attr_filter.get("slug"):
            attr = attributes_map[attr_slug]
            attr_id = attr.id

        attr_value = attr_filter["value"]

        if "slug" in attr_value or "name" in attr_value:
            attr_filter_expression &= filter_by_slug_or_name(
                attr_id,
                attr_value,
                qs.db,
            )
        elif "numeric" in attr_value:
            attr_filter_expression &= filter_by_numeric_attribute(
                attr_id,
                attr_value["numeric"],
                qs.db,
            )
        elif "boolean" in attr_value:
            attr_filter_expression &= filter_by_boolean_attribute(
                attr_id,
                attr_value["boolean"],
                qs.db,
            )
        elif "date" in attr_value:
            attr_filter_expression &= filter_by_date_attribute(
                attr_id,
                attr_value["date"],
                qs.db,
            )
        elif "date_time" in attr_value:
            attr_filter_expression &= filter_by_date_time_attribute(
                attr_id,
                attr_value["date_time"],
                qs.db,
            )
        elif "reference" in attr_value:
            attr_filter_expression &= filter_objects_by_reference_attributes(
                attr_id,
                attr_value["reference"],
                qs.db,
            )
    return qs.filter(attr_filter_expression)


class ProductVariantFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method="product_variant_filter_search")
    sku = ListObjectTypeFilter(input_class=graphene.String, method=filter_sku_list)
    is_preorder = django_filters.BooleanFilter(method=filter_is_preorder)
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at_range
    )

    class Meta:
        model = ProductVariant
        fields = ["search", "sku"]

    def product_variant_filter_search(self, queryset, _name, value):
        if not value:
            return queryset
        qs = Q(name__ilike=value) | Q(sku__ilike=value)
        products = (
            Product.objects.using(queryset.db).filter(name__ilike=value).values("pk")
        )
        qs |= Q(Exists(products.filter(variants=OuterRef("pk"))))
        return queryset.filter(qs)


class ProductVariantWhere(MetadataWhereFilterBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("ProductVariant"))
    sku = ObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_product_sku",
        help_text="Filter by product SKU.",
    )
    updated_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method="filter_updated_at",
        help_text="Filter by when was the most recent update.",
    )
    attributes = ListObjectTypeWhereFilter(
        input_class=AssignedAttributeWhereInput,
        method="filter_attributes",
        help_text="Filter by attributes associated with the variant." + ADDED_IN_322,
    )

    class Meta:
        model = ProductVariant
        fields = []

    @staticmethod
    def filter_product_sku(qs, _, value):
        return filter_where_by_value_field(qs, "sku", value)

    @staticmethod
    def filter_updated_at(qs, _, value):
        return filter_where_by_range_field(qs, "updated_at", value)

    @staticmethod
    def filter_attributes(qs, _, value):
        if not value:
            return qs
        return filter_variants_by_attributes(qs, value)

    def is_valid(self):
        if attributes := self.data.get("attributes"):
            validate_attribute_value_input(attributes, self.queryset.db)
        return super().is_valid()


class ProductVariantFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductVariantFilter


class ProductVariantWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductVariantWhere
