import datetime
import math
from collections import defaultdict
from typing import TypedDict

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
    filter_objects_by_attributes,
    validate_attribute_value_input,
)

T_PRODUCT_FILTER_QUERIES = dict[int, list[int]]


def _clean_product_attributes_filter_input(
    filter_values, field, queries, database_connection_name
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

    values_map = _populate_value_map(
        database_connection_name, field, values, attributes, attributes_pk_slug_map
    )

    _update_queries(queries, filter_values, attributes_slug_pk_map, values_map)


def _populate_value_map(
    database_connection_name, field, values, attribute_qs, attributes_pk_slug_map
):
    value_maps: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for (
        attr_pk,
        value_pk,
        field_value,
    ) in (
        AttributeValue.objects.using(database_connection_name)
        .filter(Exists(attribute_qs.filter(pk=OuterRef("attribute_id"))))
        .filter(**{f"{field}__in": values})
        .values_list("attribute_id", "pk", field)
    ):
        attr_slug = attributes_pk_slug_map[attr_pk]
        value_maps[attr_slug][field_value].append(value_pk)

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
    filter_name_values,
    filter_range_values,
    filter_boolean_values,
    date_range_list,
    date_time_range_list,
):
    queries: dict[int, list[int]] = defaultdict(list)
    try:
        if filter_slug_values:
            _clean_product_attributes_filter_input(
                filter_slug_values, "slug", queries, qs.db
            )
        if filter_name_values:
            _clean_product_attributes_filter_input(
                filter_name_values, "name", queries, qs.db
            )
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
    name_value_list = []
    boolean_list = []
    value_range_list = []
    date_range_list = []
    date_time_range_list = []

    for v in value:
        slug = v["slug"]
        if "values" in v:
            slug_value_list.append((slug, v["values"]))
        elif "value_names" in v:
            name_value_list.append((slug, v["value_names"]))
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
        name_value_list,
        value_range_list,
        boolean_list,
        date_range_list,
        date_time_range_list,
    )
    return qs


def _filter_products_by_attributes(qs, value):
    return filter_objects_by_attributes(
        qs,
        value,
        AssignedProductAttributeValue,
        "product_id",
    )


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
