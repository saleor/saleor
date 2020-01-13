from typing import Any, Dict, Union
import graphene
import opentracing as ot
from django.db.models import Manager, QuerySet
from graphene import Field, List, NonNull, ObjectType, String
from graphene.relay.connection import Connection
from graphene_django_optimizer.types import OptimizedDjangoObjectType
from graphql_relay.connection.arrayconnection import (
    get_offset_with_default,
    offset_to_cursor,
)
from graphql_relay.connection.connectiontypes import Edge, PageInfo

ConnectionArguments = Dict[str, Any]


def connection_from_queryset_slice(
    qs: QuerySet,
    args: ConnectionArguments = None,
    connection_type: Any = Connection,
    edge_type: Any = Edge,
    page_info_type: Any = PageInfo,
) -> Connection:
    """Create a connection object from a QuerySet."""
    args = args or {}
    before = args.get("before")
    after = args.get("after")
    first = args.get("first")
    last = args.get("last")
    before_offset = get_offset_with_default(before, None)
    after_offset = get_offset_with_default(after, None)

    start_offset = max(0, after_offset or 0)
    end_offset = before_offset or None
    requested_count = end_offset - start_offset if end_offset else None

    if isinstance(first, int):
        if first < 0:
            raise ValueError("Argument 'first' must be a non-negative integer.")

        requested_end_offset = start_offset + first
        end_offset = (
            min(end_offset, requested_end_offset)
            if end_offset
            else requested_end_offset
        )
        requested_count = end_offset - start_offset

    if isinstance(last, int):
        if last < 0:
            raise ValueError("Argument 'last' must be a non-negative integer.")
        if isinstance(first, int):
            raise ValueError("Argument 'last' cannot be combined with 'first'.")
        if not end_offset:
            raise ValueError("Argument 'last' requires 'before' to be specified.")

        start_offset = max(start_offset, end_offset - last)
        requested_count = end_offset - start_offset

    previous_page_margin = 1 if start_offset > 0 else 0

    matching_records = list(
        qs[start_offset - previous_page_margin : end_offset + 1]
        if end_offset
        else qs[start_offset - previous_page_margin :]
    )

    has_previous_page = False
    has_next_page = False
    if previous_page_margin:
        has_previous_page = len(matching_records) > 0
        matching_records = matching_records[previous_page_margin:]
    if requested_count is not None:
        has_next_page = len(matching_records) > requested_count
        matching_records = matching_records[:requested_count]

    edges = [
        edge_type(node=value, cursor=offset_to_cursor(start_offset + index))
        for index, value in enumerate(matching_records)
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
        return len(root.iterable)


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
    def maybe_optimize(cls, info, qs: Union[QuerySet, Manager], pk):
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
