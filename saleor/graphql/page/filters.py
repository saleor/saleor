from typing import Literal

import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q, QuerySet

from ...attribute.models import AssignedPageAttributeValue, Attribute, AttributeValue
from ...page import models
from ..attribute.shared_filters import (
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
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
)
from ..core.filters.where_filters import (
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeWhereFilter,
    MetadataWhereBase,
    OperationObjectTypeWhereFilter,
)
from ..core.filters.where_input import (
    GlobalIDFilterInput,
    StringFilterInput,
    WhereInputObjectType,
)
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import (
    Number,
    filter_by_id,
    filter_by_ids,
    filter_slug_list,
    filter_where_by_id_field,
    filter_where_by_value_field,
)
from .types import Page, PageType


def filter_page_page_types(qs, _, value):
    if not value:
        return qs
    _, page_types_pks = resolve_global_ids_to_primary_keys(value, PageType)
    return qs.filter(page_type_id__in=page_types_pks)


def filter_page_type_search(qs, _, value):
    if not value:
        return qs
    return qs.filter(Q(name__trigram_similar=value) | Q(slug__trigram_similar=value))


def _get_assigned_page_attribute_for_attribute_value(
    attribute_values: QuerySet[AttributeValue],
    db_connection_name: str,
):
    return Q(
        Exists(
            AssignedPageAttributeValue.objects.using(db_connection_name).filter(
                Exists(attribute_values.filter(id=OuterRef("value_id"))),
                page_id=OuterRef("id"),
            )
        )
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
    return _get_assigned_page_attribute_for_attribute_value(
        attribute_values=attribute_values,
        db_connection_name=db_connection_name,
    )


def filter_by_numeric_attribute(
    attr_id: int | None,
    numeric_value: dict[str, Number | list[Number] | dict[str, Number]],
    db_connection_name: str,
):
    attribute_values = get_attribute_values_by_numeric_value(
        attr_id=attr_id,
        numeric_value=numeric_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_page_attribute_for_attribute_value(
        attribute_values=attribute_values,
        db_connection_name=db_connection_name,
    )


def filter_by_boolean_attribute(
    attr_id: int | None,
    boolean_value: bool,
    db_connection_name: str,
):
    attribute_values = get_attribute_values_by_boolean_value(
        attr_id=attr_id,
        boolean_value=boolean_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_page_attribute_for_attribute_value(
        attribute_values=attribute_values,
        db_connection_name=db_connection_name,
    )


def filter_by_date_attribute(
    attr_id: int | None,
    date_value: dict[str, str],
    db_connection_name: str,
):
    attribute_values = get_attribute_values_by_date_value(
        attr_id=attr_id,
        date_value=date_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_page_attribute_for_attribute_value(
        attribute_values=attribute_values,
        db_connection_name=db_connection_name,
    )


def filter_by_date_time_attribute(
    attr_id: int | None,
    date_value: dict[str, str],
    db_connection_name: str,
):
    attribute_values = get_attribute_values_by_date_time_value(
        attr_id=attr_id,
        date_value=date_value,
        db_connection_name=db_connection_name,
    )
    return _get_assigned_page_attribute_for_attribute_value(
        attribute_values=attribute_values,
        db_connection_name=db_connection_name,
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
    return _get_assigned_page_attribute_for_attribute_value(
        referenced_attr_values,
        db_connection_name,
    )


def filter_by_contains_referenced_page_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter pages based on their references to pages.

    - If `contains_all` is provided, only pages that reference all of the
    specified pages will match.
    - If `contains_any` is provided, pages that reference at least one of
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


def filter_by_contains_referenced_product_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter pages based on their references to products.

    - If `contains_all` is provided, only pages that reference all of the
    specified products will match.
    - If `contains_any` is provided, pages that reference at least one of
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


def filter_by_contains_referenced_category_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter pages based on their references to categories.

    - If `contains_all` is provided, only pages that reference all of the
    specified categories will match.
    - If `contains_any` is provided, pages that reference at least one of
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
    """Build an expression to filter pages based on their references to collections.

    - If `contains_all` is provided, only pages that reference all of the
    specified collections will match.
    - If `contains_any` is provided, pages that reference at least one of
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


def filter_by_contains_referenced_variant_skus(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter pages based on their references to variants.

    - If `contains_all` is provided, only pages that reference all of the
    specified variants will match.
    - If `contains_any` is provided, pages that reference at least one of
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


def filter_pages_by_attributes(qs, value):
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
        assigned_attr_value = AssignedPageAttributeValue.objects.using(qs.db).filter(
            Exists(atr_value_qs.filter(id=OuterRef("value_id"))),
            page_id=OuterRef("id"),
        )
        attr_filter_expression = Q(Exists(assigned_attr_value))

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
    if attr_filter_expression != Q():
        return qs.filter(attr_filter_expression)
    return qs.none()


class PageWhere(MetadataWhereBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Page"))
    slug = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_page_slug",
        help_text="Filter by page slug.",
    )
    page_type = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_page_type",
        help_text="Filter by page type.",
    )
    attributes = ListObjectTypeWhereFilter(
        input_class=AssignedAttributeWhereInput,
        method="filter_attributes",
        help_text="Filter by attributes associated with the page.",
    )

    @staticmethod
    def filter_page_slug(qs, _, value):
        return filter_where_by_value_field(qs, "slug", value)

    @staticmethod
    def filter_page_type(qs, _, value):
        if not value:
            return qs
        return filter_where_by_id_field(qs, "page_type", value, "PageType")

    @staticmethod
    def filter_attributes(qs, _, value):
        if not value:
            return qs
        return filter_pages_by_attributes(qs, value)

    def is_valid(self):
        if attributes := self.data.get("attributes"):
            validate_attribute_value_input(attributes, self.queryset.db)
        return super().is_valid()


def filter_page_search(qs, _, value):
    # Skip search, as search is applied on resolver side.
    return qs


class PageFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method=filter_page_search)
    page_types = GlobalIDMultipleChoiceFilter(method=filter_page_page_types)
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id(Page))
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = models.Page
        fields = ["search"]


class PageFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        filterset_class = PageFilter


class PageWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        filterset_class = PageWhere


class PageTypeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_page_type_search)
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)


class PageTypeFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        filterset_class = PageTypeFilter
