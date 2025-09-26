import datetime
import math
from collections import defaultdict
from typing import Literal, TypedDict

from django.db.models import Exists, OuterRef, Q, QuerySet
from graphql import GraphQLError

from ....attribute import AttributeInputType
from ....attribute.models import (
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    Attribute,
    AttributeValue,
)
from ....product.models import Product, ProductVariant
from ...attribute.shared_filters import (
    CONTAINS_TYPING,
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
from ...utils.filters import Number

T_PRODUCT_FILTER_QUERIES = dict[int, list[int]]


def _clean_product_attributes_filter_input(
    filter_values, queries, database_connection_name
):
    attribute_slugs = []
    values = []

    for attr_slug, field_value in filter_values:
        attribute_slugs.append(attr_slug)
        values.extend(field_value)

    attributes_slug_pk_map: dict[str, int] = {}
    attributes_pk_slug_map: dict[int, str] = {}
    attributes = Attribute.objects.using(database_connection_name).filter(
        slug__in=attribute_slugs
    )
    for attr_slug, attr_pk in attributes.values_list("slug", "id"):
        attributes_slug_pk_map[attr_slug] = attr_pk
        attributes_pk_slug_map[attr_pk] = attr_slug

    values_map = _populate_slug_value_map(
        database_connection_name, values, attributes, attributes_pk_slug_map
    )

    _update_queries(queries, filter_values, attributes_slug_pk_map, values_map)


def _populate_slug_value_map(
    database_connection_name, slugs, attribute_qs, attributes_pk_slug_map
):
    value_maps: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for (
        attr_pk,
        value_pk,
        value_slug,
    ) in (
        AttributeValue.objects.using(database_connection_name)
        .filter(Exists(attribute_qs.filter(pk=OuterRef("attribute_id"))))
        .filter(slug__in=slugs)
        .values_list("attribute_id", "pk", "slug")
    ):
        attr_slug = attributes_pk_slug_map[attr_pk]
        value_maps[attr_slug][value_slug].append(value_pk)

    return value_maps


def _update_queries(queries, filter_values, attributes_slug_pk_map, value_maps):
    for attr_name, vals in filter_values:
        if attr_name not in attributes_slug_pk_map:
            raise ValueError(f"Unknown attribute name: {attr_name}")
        attr_pk = attributes_slug_pk_map[attr_name]
        attr_val_pk = []
        for val in vals:
            if val in value_maps[attr_name]:
                attr_val_pk.extend(value_maps[attr_name][val])
        queries[attr_pk] += attr_val_pk


def _clean_product_attributes_range_filter_input(
    filter_value, queries, database_connection_name
):
    attributes = Attribute.objects.using(database_connection_name).filter(
        input_type=AttributeInputType.NUMERIC
    )
    values = (
        AttributeValue.objects.using(database_connection_name)
        .filter(
            Exists(attributes.filter(pk=OuterRef("attribute_id"))),
            numeric__isnull=False,
        )
        .select_related("attribute")
    )

    attributes_map: dict[str, int] = {}
    values_map: defaultdict[str, defaultdict[float, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for value_data in values.values_list(
        "attribute_id", "attribute__slug", "pk", "numeric"
    ):
        attr_pk, attr_slug, pk, numeric_value = value_data
        attributes_map[attr_slug] = attr_pk
        if not numeric_value:
            continue
        values_map[attr_slug][numeric_value].append(pk)

    for attr_name, val_range in filter_value:
        if attr_name not in attributes_map:
            raise ValueError(f"Unknown numeric attribute name: {attr_name}")
        gte, lte = val_range.get("gte", 0), val_range.get("lte", math.inf)
        attr_pk = attributes_map[attr_name]
        attr_values = values_map[attr_name]
        matching_values = [
            value for value in attr_values.keys() if gte <= value and lte >= value
        ]
        queries[attr_pk] = []
        for value in matching_values:
            queries[attr_pk] += attr_values[value]


def _clean_product_attributes_date_time_range_filter_input(
    filter_value, database_connection_name
):
    attribute_slugs = [slug for slug, _ in filter_value]
    matching_attributes = AttributeValue.objects.using(database_connection_name).filter(
        attribute__slug__in=attribute_slugs
    )
    filters = {}
    for _, val_range in filter_value:
        if lte := val_range.get("lte"):
            if not isinstance(lte, datetime.datetime):
                lte = datetime.datetime.combine(
                    lte, datetime.datetime.max.time(), tzinfo=datetime.UTC
                )
            filters["date_time__lte"] = lte
        if gte := val_range.get("gte"):
            if not isinstance(gte, datetime.datetime):
                gte = datetime.datetime.combine(
                    gte, datetime.datetime.min.time(), tzinfo=datetime.UTC
                )
            filters["date_time__gte"] = gte
    return matching_attributes.filter(**filters)


class KeyValueDict(TypedDict):
    pk: int
    values: dict[bool | None, int]


def _clean_product_attributes_boolean_filter_input(
    filter_value, queries, database_connection_name
):
    attribute_slugs = [slug for slug, _ in filter_value]
    attributes = (
        Attribute.objects.using(database_connection_name)
        .filter(input_type=AttributeInputType.BOOLEAN, slug__in=attribute_slugs)
        .prefetch_related("values")
    )
    values_map: dict[str, KeyValueDict] = {
        attr.slug: {
            "pk": attr.pk,
            "values": {val.boolean: val.pk for val in attr.values.all()},
        }
        for attr in attributes
    }

    for attr_slug, value in filter_value:
        if attr_slug not in values_map:
            raise ValueError(f"Unknown attribute name: {attr_slug}")
        attr_pk = values_map[attr_slug].get("pk")
        value_pk = values_map[attr_slug]["values"].get(value)
        if not value_pk:
            raise ValueError(f"Requested value for attribute {attr_slug} doesn't exist")
        if attr_pk and value_pk:
            queries[attr_pk] += [value_pk]


def filter_products_by_attributes_values(qs, queries: T_PRODUCT_FILTER_QUERIES):
    filters = []
    for values in queries.values():
        assigned_product_attribute_values = AssignedProductAttributeValue.objects.using(
            qs.db
        ).filter(value_id__in=values)
        product_attribute_filter = Q(
            Exists(assigned_product_attribute_values.filter(product_id=OuterRef("pk")))
        )

        assigned_variant_attribute_values = AssignedVariantAttributeValue.objects.using(
            qs.db
        ).filter(value_id__in=values)
        assigned_variant_attributes = AssignedVariantAttribute.objects.using(
            qs.db
        ).filter(
            Exists(
                assigned_variant_attribute_values.filter(assignment_id=OuterRef("pk"))
            )
        )
        product_variants = ProductVariant.objects.using(qs.db).filter(
            Exists(assigned_variant_attributes.filter(variant_id=OuterRef("pk")))
        )
        variant_attribute_filter = Q(
            Exists(product_variants.filter(product_id=OuterRef("pk")))
        )

        filters.append(product_attribute_filter | variant_attribute_filter)

    return qs.filter(*filters)


def filter_products_by_attributes_values_qs(qs, values_qs):
    assigned_product_attribute_values = AssignedProductAttributeValue.objects.using(
        qs.db
    ).filter(value__in=values_qs)
    product_attribute_filter = Q(
        Exists(assigned_product_attribute_values.filter(product_id=OuterRef("pk")))
    )

    assigned_variant_attribute_values = AssignedVariantAttributeValue.objects.using(
        qs.db
    ).filter(value__in=values_qs)
    assigned_variant_attributes = AssignedVariantAttribute.objects.using(qs.db).filter(
        Exists(assigned_variant_attribute_values.filter(assignment_id=OuterRef("pk")))
    )
    product_variants = ProductVariant.objects.using(qs.db).filter(
        Exists(assigned_variant_attributes.filter(variant_id=OuterRef("pk")))
    )
    variant_attribute_filter = Q(
        Exists(product_variants.filter(product_id=OuterRef("pk")))
    )

    return qs.filter(product_attribute_filter | variant_attribute_filter)


def _filter_products_by_deprecated_attributes_input(
    qs,
    filter_slug_values,
    filter_range_values,
    filter_boolean_values,
    date_range_list,
    date_time_range_list,
):
    queries: dict[int, list[int]] = defaultdict(list)
    try:
        if filter_slug_values:
            _clean_product_attributes_filter_input(filter_slug_values, queries, qs.db)
        if filter_range_values:
            _clean_product_attributes_range_filter_input(
                filter_range_values, queries, qs.db
            )
        if date_range_list:
            values_qs = _clean_product_attributes_date_time_range_filter_input(
                date_range_list, qs.db
            )
            return filter_products_by_attributes_values_qs(qs, values_qs)
        if date_time_range_list:
            values_qs = _clean_product_attributes_date_time_range_filter_input(
                date_time_range_list, qs.db
            )
            return filter_products_by_attributes_values_qs(qs, values_qs)
        if filter_boolean_values:
            _clean_product_attributes_boolean_filter_input(
                filter_boolean_values, queries, qs.db
            )
    except ValueError:
        return Product.objects.none()
    return filter_products_by_attributes_values(qs, queries)


def deprecated_filter_attributes(qs, value):
    if not value:
        return qs.none()

    slug_value_list = []
    boolean_list = []
    value_range_list = []
    date_range_list = []
    date_time_range_list = []

    for v in value:
        slug = v["slug"]
        if "values" in v:
            slug_value_list.append((slug, v["values"]))
        elif "values_range" in v:
            value_range_list.append((slug, v["values_range"]))
        elif "date" in v:
            date_range_list.append((slug, v["date"]))
        elif "date_time" in v:
            date_time_range_list.append((slug, v["date_time"]))
        elif "boolean" in v:
            boolean_list.append((slug, v["boolean"]))

    qs = _filter_products_by_deprecated_attributes_input(
        qs,
        slug_value_list,
        value_range_list,
        boolean_list,
        date_range_list,
        date_time_range_list,
    )
    return qs


def _get_assigned_product_attribute_for_attribute_value(
    attribute_values: QuerySet[AttributeValue],
    db_connection_name: str,
):
    return Q(
        Exists(
            AssignedProductAttributeValue.objects.using(db_connection_name).filter(
                Exists(attribute_values.filter(id=OuterRef("value_id"))),
                product_id=OuterRef("id"),
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
    return _get_assigned_product_attribute_for_attribute_value(
        attribute_values=attribute_values,
        db_connection_name=db_connection_name,
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
    return _get_assigned_product_attribute_for_attribute_value(
        attribute_values=qs_by_numeric,
        db_connection_name=db_connection_name,
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
    return _get_assigned_product_attribute_for_attribute_value(
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
    return _get_assigned_product_attribute_for_attribute_value(
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
    return _get_assigned_product_attribute_for_attribute_value(
        qs_by_date_time,
        db_connection_name,
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
    return _get_assigned_product_attribute_for_attribute_value(
        referenced_attr_values,
        db_connection_name,
    )


def filter_by_contains_referenced_page_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter products based on their references to pages.

    - If `contains_all` is provided, only products that reference all of the
    specified pages will match.
    - If `contains_any` is provided, products that reference at least one of
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
    """Build an expression to filter products based on their references to products.

    - If `contains_all` is provided, only products that reference all of the
    specified products will match.
    - If `contains_any` is provided, products that reference at least one of
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
    """Build an expression to filter products based on their references to variants.

    - If `contains_all` is provided, only products that reference all of the
    specified variants will match.
    - If `contains_any` is provided, products that reference at least one of
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


def filter_by_contains_referenced_category_slugs(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
):
    """Build an expression to filter products based on their references to categories.

    - If `contains_all` is provided, only products that reference all of the
    specified categories will match.
    - If `contains_any` is provided, products that reference at least one of
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
    """Build an expression to filter products based on their references to collections.

    - If `contains_all` is provided, only products that reference all of the
    specified collections will match.
    - If `contains_any` is provided, products that reference at least one of
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


def _filter_products_by_attributes(
    qs: QuerySet[Product], value: list[dict]
) -> QuerySet[Product]:
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
        attr_filter_expression = _get_assigned_product_attribute_for_attribute_value(
            atr_value_qs, qs.db
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
    if attr_filter_expression != Q():
        return qs.filter(attr_filter_expression)
    return qs.none()


def validate_attribute_input(attributes: list[dict], db_connection_name: str):
    value_used_with_deprecated_input = []
    missing_slug_for_deprecated_input: list[str] = []

    used_deprecated_filter = [
        # When input contains other fields than slug and value
        bool(set(attr_data.keys()).difference({"slug", "value"}))
        for attr_data in attributes
    ]
    mixed_filter_usage = len(set(used_deprecated_filter)) > 1
    if mixed_filter_usage:
        raise GraphQLError(
            "The provided `attributes` input contains a mix of deprecated fields"
            "and `value`. Please use either the `AttributeInput.value` field "
            "exclusively or only the deprecated fields."
        )

    for index, attr_data in enumerate(attributes):
        if set(attr_data.keys()).difference({"slug", "value"}):
            # Input contains deprecated input values
            if not attr_data.get("slug"):
                missing_slug_for_deprecated_input.append(str(index))
                continue
            if "value" in attr_data:
                value_used_with_deprecated_input.append(str(index))
                continue
    if missing_slug_for_deprecated_input:
        raise GraphQLError(
            "Attribute `slug` is required when using deprecated fields in "
            "the `attributes` input. "
            f"Missing at indices: {', '.join(missing_slug_for_deprecated_input)}."
        )
    if value_used_with_deprecated_input:
        raise GraphQLError(
            "The `value` field cannot be used with deprecated fields in "
            "the `attributes` input. "
            f"Used at indices: {', '.join(value_used_with_deprecated_input)}."
        )

    validate_attribute_value_input(attributes, db_connection_name)


def filter_products_by_attributes(
    qs: QuerySet[Product], value: list[dict[str, str | dict | list | bool]]
) -> QuerySet[Product]:
    if not value:
        return qs.none()

    if set(value[0].keys()).difference({"slug", "value"}):
        return deprecated_filter_attributes(qs, value)
    return _filter_products_by_attributes(qs, value)
