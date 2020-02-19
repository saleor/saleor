import typing

import graphene
import opentracing as ot
from django.db.models import Model as DjangoModel, Q, QuerySet, Manager
from graphene import Field, List, NonNull, ObjectType, String
from graphene.relay.connection import Connection
from graphene_django_optimizer.types import OptimizedDjangoObjectType
from graphql_relay.connection.connectiontypes import Edge, PageInfo
from graphql_relay.utils import base64, unbase64

from ..core.enums import OrderDirection

ConnectionArguments = typing.Dict[str, typing.Any]


def to_global_cursor(values):
    if not isinstance(values, list):
        values = [str(values)]
    else:
        values = [str(value) for value in values]
    return base64(":".join(values))


def from_global_cursor(cursor) -> typing.List[str]:
    values = unbase64(cursor)
    values = values.split(":")
    if isinstance(values, list):
        return values
    return [values]


def get_field_value(instance: DjangoModel, field_name: str):
    """Get field value for given field in filter format 'field__foreign_key_field'
    """
    field_path = field_name.split("__")
    attr = instance
    for elem in field_path:
        try:
            attr = getattr(attr, elem)
        except AttributeError:
            return None

    if callable(attr):
        return "%s" % attr()
    return attr


def prepare_filter(
    cursor: typing.List, sorting_fields: typing.List, sorting_direction: str
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
        field_expression = {}
        for cursor_id, cursor_value in enumerate(cursor[:index]):
            field_expression[sorting_fields[cursor_id]] = cursor_value
        field_expression[f"{field_name}__{sorting_direction}"] = cursor[index]
        filter_kwargs |= Q(**field_expression)
    return filter_kwargs


def validate_connection_args(args):
    first = args.get("first")
    last = args.get("last")

    if first and not (isinstance(first, int) and first > 0):
        raise ValueError('Argument "first" must be a non-negative integer.')
    if last and not (isinstance(last, int) and last > 0):
        raise ValueError('Argument "last" must be a non-negative integer.')
    if first and last:
        raise ValueError('Argument "last" cannot be combined with "first".')
    if first and args.get("before"):
        raise ValueError('Argument "first" cannot be combined with "before".')
    if last and args.get("after"):
        raise ValueError('Argument "last" cannot be combined with "after".')


def connection_from_queryset_slice(
    qs: QuerySet,
    args: ConnectionArguments = None,
    connection_type: typing.Any = Connection,
    edge_type: typing.Any = Edge,
    page_info_type: typing.Any = PageInfo,
) -> Connection:
    """Create a connection object from a QuerySet."""
    args = args or {}
    before = args.get("before")
    after = args.get("after")
    first = args.get("first")
    last = args.get("last")
    validate_connection_args(args)

    cursor_after = from_global_cursor(after) if after else None
    cursor_before = from_global_cursor(before) if before else None
    cursor = cursor_after or cursor_before

    sort_by = args.get("sort_by", {})
    sorting_direction = sort_by.get("direction", "")
    sorting_fields = sort_by.get("field")
    if sorting_fields and not isinstance(sorting_fields, list):
        sorting_fields = [sorting_fields]
    elif not sorting_fields:
        raise ValueError("Error while preparing cursor values.")

    requested_count = first or last
    end_margin = requested_count + 1 if requested_count else None

    if last:
        # reversed direction
        sorting_direction = "gt" if sorting_direction == OrderDirection.DESC else "lt"
    else:
        sorting_direction = "lt" if sorting_direction == OrderDirection.DESC else "gt"

    filter_kwargs = (
        prepare_filter(cursor, sorting_fields, sorting_direction) if cursor else Q()
    )
    qs = qs.filter(filter_kwargs)[:end_margin]
    if last:
        matching_records = list(reversed(qs))
    else:
        matching_records = list(qs)
    has_previous_page = False
    has_next_page = False
    if requested_count is not None:
        if cursor_after:
            has_next_page = len(matching_records) > requested_count
            has_previous_page = True
        elif cursor_before:
            has_next_page = True
            has_previous_page = len(matching_records) > requested_count
        elif first:
            has_next_page = len(matching_records) > requested_count
        elif last:
            has_previous_page = len(matching_records) > requested_count
        matching_records = matching_records[:requested_count]

    edges = [
        edge_type(
            node=record,
            cursor=to_global_cursor(
                [get_field_value(record, field) for field in sorting_fields]
            ),
        )
        for record in matching_records
    ]

    first_edge_cursor = edges[0].cursor if edges else None
    last_edge_cursor = edges[-1].cursor if edges else None

    return connection_type(
        edges=edges,
        page_info=page_info_type(
            start_cursor=first_edge_cursor,
            end_cursor=last_edge_cursor,
            has_previous_page=has_previous_page,
            has_next_page=has_next_page,
        ),
    )


class NonNullConnection(Connection):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        super().__init_subclass_with_meta__(node=node, name=name, **options)

        # Override the original EdgeBase type to make to `node` field required.
        class EdgeBase:
            node = Field(
                cls._meta.node,
                description="The item at the end of the edge.",
                required=True,
            )
            cursor = String(
                required=True, description="A cursor for use in pagination."
            )

        # Create the edge type using the new EdgeBase.
        edge_name = cls.Edge._meta.name
        edge_bases = (EdgeBase, ObjectType)
        edge = type(edge_name, edge_bases, {})
        cls.Edge = edge

        # Override the `edges` field to make it non-null list
        # of non-null edges.
        cls._meta.fields["edges"] = Field(NonNull(List(NonNull(cls.Edge))))


class CountableConnection(NonNullConnection):
    class Meta:
        abstract = True

    total_count = graphene.Int(description="A total count of items in the collection.")

    @staticmethod
    def resolve_total_count(root, *_args, **_kwargs):
        if isinstance(root.iterable, list):
            return len(root.iterable)
        return root.iterable.count()


class CountableDjangoObjectType(OptimizedDjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        # Force it to use the countable connection
        countable_conn = CountableConnection.create_type(
            "{}CountableConnection".format(cls.__name__), node=cls
        )
        super().__init_subclass_with_meta__(*args, connection=countable_conn, **kwargs)

    @classmethod
    def maybe_optimize(cls, info, qs: typing.Union[QuerySet, Manager], pk):
        with ot.global_tracer().start_active_span("optimizer") as scope:
            span = scope.span
            span.set_tag("optimizer.pk", pk)
            span.set_tag("optimizer.model", cls._meta.model.__name__)
            return super().maybe_optimize(info, qs, pk)

    @classmethod
    def get_node(cls, info, id):
        with ot.global_tracer().start_active_span("node") as scope:
            span = scope.span
            span.set_tag("node.pk", id)
            span.set_tag("node.type", cls.__name__)
            return super().get_node(info, id)
