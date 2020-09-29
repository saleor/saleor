from typing import Tuple

from django.db.models import QuerySet
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from ..core.enums import OrderDirection
from ..core.types import SortInputObjectType

REVERSED_DIRECTION = {
    "-": "",
    "": "-",
}


def _sort_queryset_by_attribute(queryset, sorting_attribute, sorting_direction):
    if sorting_attribute != "":
        graphene_type, sorting_attribute = from_global_id(sorting_attribute)
    descending = sorting_direction == OrderDirection.DESC
    queryset = queryset.sort_by_attribute(sorting_attribute, descending=descending)
    return queryset


def sort_queryset_for_connection(iterable, args):
    sort_by = args.get("sort_by")
    reversed = True if "last" in args else False
    if sort_by:
        iterable = sort_queryset(queryset=iterable, sort_by=sort_by, reversed=reversed)
    else:
        iterable, sort_by = sort_queryset_by_default(
            queryset=iterable, reversed=reversed
        )
        args["sort_by"] = sort_by
    return iterable, sort_by


def sort_queryset(
    queryset: QuerySet, sort_by: SortInputObjectType, reversed: bool
) -> QuerySet:
    """Sort queryset according to given parameters.

    rules:
        - sorting_field and sorting_attribute cannot be together)
        - when sorting_attribute is passed, it is expected that
            queryset will have method to sort by attributes
        - when sorter has custom sorting method it's name must be like
            `prepare_qs_for_sort_{enum_name}` and it must return sorted queryset

    Keyword Arguments:
        queryset - queryset to be sorted
        sort_by - dictionary with sorting field and direction

    """
    sorting_direction = sort_by.direction
    if reversed:
        sorting_direction = REVERSED_DIRECTION[sorting_direction]

    sorting_field = sort_by.field
    sorting_attribute = getattr(sort_by, "attribute_id", None)

    if sorting_field is not None and sorting_attribute is not None:
        raise GraphQLError(
            "You must provide either `field` or `attributeId` to sort the products."
        )
    elif sorting_attribute is not None:  # empty string as sorting_attribute is valid
        return _sort_queryset_by_attribute(
            queryset, sorting_attribute, sorting_direction
        )

    sort_enum = sort_by._meta.sort_enum
    sorting_fields = sort_enum.get(sorting_field)
    sorting_field_name = sorting_fields.name.lower()

    channel_slug = getattr(sort_by, "channel", None)
    custom_sort_by = getattr(sort_enum, f"qs_with_{sorting_field_name}", None)
    if custom_sort_by:
        queryset = custom_sort_by(queryset, channel_slug=channel_slug)

    sorting_field_value = sorting_fields.value
    sorting_list = [f"{sorting_direction}{field}" for field in sorting_field_value]

    return queryset.order_by(*sorting_list)


def get_model_default_ordering(model_class):
    default_ordering = []
    model_ordering = model_class._meta.ordering
    for field in model_ordering:
        if isinstance(field, str):
            default_ordering.append(field)
        else:
            direction = "-" if field.descending else ""
            default_ordering.append(f"{direction}{field.expression.name}")
    return default_ordering


def sort_queryset_by_default(
    queryset: QuerySet, reversed: bool
) -> Tuple[QuerySet, dict]:
    """Sort queryset by it's default ordering."""
    queryset_model = queryset.model
    default_ordering = ["pk"]
    if queryset_model and queryset_model._meta.ordering:
        default_ordering = get_model_default_ordering(queryset_model)

    ordering_fields = [field.replace("-", "") for field in default_ordering]
    direction = "-" if "-" in default_ordering[0] else ""
    if reversed:
        reversed_direction = REVERSED_DIRECTION[direction]
        default_ordering = [f"{reversed_direction}{field}" for field in ordering_fields]

    order_by = {"field": ordering_fields, "direction": direction}
    return queryset.order_by(*default_ordering), order_by
