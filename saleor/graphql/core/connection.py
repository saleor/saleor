import json
from typing import Any, Dict, Iterable, List, Tuple, Union

import graphene
from django.db.models import Model as DjangoModel
from django.db.models import Q, QuerySet
from graphene.relay.connection import Connection
from graphene_django.types import DjangoObjectType
from graphql.error import GraphQLError
from graphql_relay.connection.connectiontypes import Edge, PageInfo
from graphql_relay.utils import base64, unbase64

from ..core.enums import OrderDirection

ConnectionArguments = Dict[str, Any]


def to_global_cursor(values):
    if not isinstance(values, Iterable):
        values = [values]
    values = [value if value is None else str(value) for value in values]
    return base64(json.dumps(values))


def from_global_cursor(cursor) -> List[str]:
    values = unbase64(cursor)
    return json.loads(values)


def get_field_value(instance: DjangoModel, field_name: str):
    """Get field value for given field in filter format 'field__foreign_key_field'."""
    field_path = field_name.split("__")
    attr = instance
    for elem in field_path:
        attr = getattr(attr, elem)

    if callable(attr):
        return "%s" % attr()
    return attr


def _prepare_filter_expression(
    field_name: str,
    index: int,
    cursor: List[str],
    sorting_fields: List[str],
    sorting_direction: str,
) -> Tuple[Q, Dict[str, Union[str, bool]]]:

    field_expression: Dict[str, Union[str, bool]] = {}
    extra_expression = Q()
    for cursor_id, cursor_value in enumerate(cursor[:index]):
        field_expression[sorting_fields[cursor_id]] = cursor_value

    if sorting_direction == "gt":
        extra_expression |= Q(**{f"{field_name}__{sorting_direction}": cursor[index]})
        extra_expression |= Q(**{f"{field_name}__isnull": True})
    elif cursor[index] is not None:
        field_expression[f"{field_name}__{sorting_direction}"] = cursor[index]
    else:
        field_expression[f"{field_name}__isnull"] = False

    return extra_expression, field_expression


def _prepare_filter(
    cursor: List[str], sorting_fields: List[str], sorting_direction: str
) -> Q:
    """Create filter arguments based on sorting fields.

    :param cursor: list of values that are passed from page_info, used for filtering.
    :param sorting_fields: list of fields that were used for sorting.
    :param sorting_direction: keyword direction ('lt', gt').
    :return: Q() in following format
        (OR: ('first_field__gt', 'first_value_form_cursor'),
            (AND: ('second_field__gt', 'second_value_form_cursor'),
                ('first_field', 'first_value_form_cursor')),
            (AND: ('third_field__gt', 'third_value_form_cursor'),
                ('second_field', 'second_value_form_cursor'),
                ('first_field', 'first_value_form_cursor'))
        )
    """
    filter_kwargs = Q()
    for index, field_name in enumerate(sorting_fields):
        if cursor[index] is None and sorting_direction == "gt":
            continue

        extra_expression, field_expression = _prepare_filter_expression(
            field_name, index, cursor, sorting_fields, sorting_direction
        )
        filter_kwargs |= Q(extra_expression, **field_expression)

    return filter_kwargs


def _validate_connection_args(args):
    first = args.get("first")
    last = args.get("last")

    if first and not (isinstance(first, int) and first > 0):
        raise GraphQLError("Argument `first` must be a non-negative integer.")
    if last and not (isinstance(last, int) and last > 0):
        raise GraphQLError("Argument `last` must be a non-negative integer.")
    if first and last:
        raise GraphQLError("Argument `last` cannot be combined with `first`.")
    if first and args.get("before"):
        raise GraphQLError("Argument `first` cannot be combined with `before`.")
    if last and args.get("after"):
        raise GraphQLError("Argument `last` cannot be combined with `after`.")


def _get_sorting_fields(sort_by, qs):
    sorting_fields = sort_by.get("field")
    sorting_attribute = sort_by.get("attribute_id")
    if sorting_fields and not isinstance(sorting_fields, list):
        return [sorting_fields]
    elif not sorting_fields and sorting_attribute is not None:
        return qs.model.sort_by_attribute_fields()
    elif not sorting_fields:
        raise ValueError("Error while preparing cursor values.")
    return sorting_fields


def _get_sorting_direction(sort_by, last=None):
    direction = sort_by.get("direction", "")
    sorting_desc = direction == OrderDirection.DESC
    if last:
        sorting_desc = not sorting_desc
    return "lt" if sorting_desc else "gt"


def _get_page_info(matching_records, cursor, first, last):
    requested_count = first or last
    page_info = {
        "has_previous_page": False,
        "has_next_page": False,
        "start_cursor": None,
        "end_cursor": None,
    }
    records_left = False
    if requested_count is not None:
        records_left = len(matching_records) > requested_count
    has_pages_before = True if cursor else False
    if first:
        page_info["has_next_page"] = records_left
        page_info["has_previous_page"] = has_pages_before
    elif last:
        page_info["has_next_page"] = has_pages_before
        page_info["has_previous_page"] = records_left

    return page_info


def _get_edges_for_connection(edge_type, qs, args, sorting_fields):
    before = args.get("before")
    after = args.get("after")
    first = args.get("first")
    last = args.get("last")
    cursor = after or before
    requested_count = first or last

    if last:
        start_slice, end_slice = 1, None
    else:
        start_slice, end_slice = 0, requested_count

    matching_records = list(qs)
    if last:
        matching_records = list(reversed(matching_records))
        if len(matching_records) <= requested_count:
            start_slice = 0
    page_info = _get_page_info(matching_records, cursor, first, last)
    matching_records = matching_records[start_slice:end_slice]

    edges = [
        edge_type(
            node=record,
            cursor=to_global_cursor(
                [get_field_value(record, field) for field in sorting_fields]
            ),
        )
        for record in matching_records
    ]
    if edges:
        page_info["start_cursor"] = edges[0].cursor
        page_info["end_cursor"] = edges[-1].cursor
    return edges, page_info


def connection_from_queryset_slice(
    qs: QuerySet,
    args: ConnectionArguments = None,
    connection_type: Any = Connection,
    edge_type: Any = Edge,
    pageinfo_type: Any = PageInfo,
) -> Connection:
    """Create a connection object from a QuerySet."""
    args = args or {}
    before = args.get("before")
    after = args.get("after")
    first = args.get("first")
    last = args.get("last")
    _validate_connection_args(args)

    requested_count = first or last
    end_margin = requested_count + 1 if requested_count else None
    cursor = after or before
    cursor = from_global_cursor(cursor) if cursor else None

    sort_by = args.get("sort_by", {})
    sorting_fields = _get_sorting_fields(sort_by, qs)
    sorting_direction = _get_sorting_direction(sort_by, last)
    if cursor and len(cursor) != len(sorting_fields):
        raise GraphQLError("Received cursor is invalid.")
    filter_kwargs = (
        _prepare_filter(cursor, sorting_fields, sorting_direction) if cursor else Q()
    )
    qs = qs.filter(filter_kwargs)
    qs = qs[:end_margin]
    edges, page_info = _get_edges_for_connection(edge_type, qs, args, sorting_fields)

    return connection_type(
        edges=edges,
        page_info=pageinfo_type(**page_info),
    )


class NonNullConnection(Connection):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        super().__init_subclass_with_meta__(node=node, name=name, **options)

        # Override the original EdgeBase type to make to `node` field required.
        class EdgeBase:
            node = graphene.Field(
                cls._meta.node,
                description="The item at the end of the edge.",
                required=True,
            )
            cursor = graphene.String(
                required=True, description="A cursor for use in pagination."
            )

        # Create the edge type using the new EdgeBase.
        edge_name = cls.Edge._meta.name
        edge_bases = (EdgeBase, graphene.ObjectType)
        edge = type(edge_name, edge_bases, {})
        cls.Edge = edge

        # Override the `edges` field to make it non-null list
        # of non-null edges.
        cls._meta.fields["edges"] = graphene.Field(
            graphene.NonNull(graphene.List(graphene.NonNull(cls.Edge)))
        )


class CountableConnection(NonNullConnection):
    class Meta:
        abstract = True

    total_count = graphene.Int(description="A total count of items in the collection.")

    @staticmethod
    def resolve_total_count(root, *_args, **_kwargs):
        if isinstance(root.iterable, list):
            return len(root.iterable)
        return root.iterable.count()


class CountableDjangoObjectType(DjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        # Force it to use the countable connection
        countable_conn = CountableConnection.create_type(
            "{}CountableConnection".format(cls.__name__), node=cls
        )
        super().__init_subclass_with_meta__(*args, connection=countable_conn, **kwargs)
